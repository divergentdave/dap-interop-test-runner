import base64
import contextlib
import io
import os
import shutil
from urllib.parse import urljoin
import tarfile
from typing import List, Union

import docker  # type: ignore
import requests
import requests.adapters


class GeneratorStreamAdapter(io.RawIOBase):
    def __init__(self, gen):
        self.gen = gen
        self.remainder = b""

    def readable(self):
        return True

    def readinto(self, buffer):
        if self.remainder:
            chunk = self.remainder
        else:
            try:
                chunk = next(self.gen)
            except StopIteration:
                return 0

        if len(chunk) <= len(buffer):
            length = len(chunk)
            buffer[:length] = chunk
            self.remainder = b""
            return length
        else:
            length = len(buffer)
            buffer[:length] = chunk[:length]
            self.remainder = chunk[length:]
            return length


class DAPContainer:
    def __init__(self, container, image):
        # Save the original image and tag for use in user-facing output. The
        # docker library will include other tags which point to the same image
        # when round-tripping through the Image class.
        self.original_image = image
        self._container = container
        self._session = requests.Session()

    def port(self) -> str:
        if not self._container.attrs["NetworkSettings"]["Ports"]:
            self._container.reload()
        fwds = self._container.attrs["NetworkSettings"]["Ports"]["8080/tcp"]
        for fwd in fwds:
            if fwd["HostIp"] == "0.0.0.0":
                return fwd["HostPort"]
        else:
            raise Exception(f"Could not find forwarded port: {fwds}")

    def host_base_url(self) -> str:
        return f"http://127.0.0.1:{self.port()}/"

    def container_base_url(self) -> str:
        return f"http://{self._container.name}:8080/"

    def make_request(self, path: str, body: dict) -> dict:
        url = self.host_base_url() + path
        response = requests.post(url, json=body)
        if response.status_code != 200:
            raise Exception(
                f"Bad status code {response.status_code} from "
                f"{self.original_image} upon {path} request: "
                f"{response.text}"
            )
        response_body = response.json()
        if response_body["status"] in ("success", "complete", "in progress"):
            return response_body
        else:
            error_message = response_body.get("error", "")
            raise Exception(
                f"Error from {self.original_image} upon {path} request: "
                f"{error_message}"
            )

    def wait_for_ready(self):
        session = requests.Session()
        session.mount(
            "http://",
            requests.adapters.HTTPAdapter(
                max_retries=requests.adapters.Retry(
                    total=10,
                    allowed_methods=["POST"],
                    backoff_factor=0.5,
                ),
            ),
        )
        url = f"{self.host_base_url()}internal/test/ready"
        response = session.post(url)
        if response.status_code == 200:
            return
        else:
            raise Exception(
                f"Container {self._container.image.tags} replied to "
                "/internal/test/ready with a status code of "
                f"{response.status_code}"
            )

    def copy_logs_directory(self, directory: str):
        gen, _stat_info = self._container.get_archive("/logs")
        stream = GeneratorStreamAdapter(gen)
        buffered_stream = io.BufferedReader(stream)
        with tarfile.open(fileobj=buffered_stream, mode="r|") as tf:
            for entry in tf:
                assert not os.path.isabs(entry.name)
                assert ".." not in entry.name
                if entry.type == tarfile.REGTYPE:
                    extract_file = tf.extractfile(entry)
                    # This shouldn't be None, we checked type == REGTYPE.
                    assert extract_file is not None

                    name = entry.name
                    if name.startswith("logs/"):
                        name = name[5:]
                    destination = os.path.join(directory, name)
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    with open(destination, "wb") as dest_file:
                        shutil.copyfileobj(extract_file, dest_file)

    def save_process_logs(self, path: str):
        # Get stdout and stderr output from the container, combined together.
        gen = self._container.logs(stream=True, follow=False)

        # Write this out to a file at the given path, only lazily creating
        # the file if the log output is non-empty.
        first_chunk = next(gen, None)
        if first_chunk is not None:
            with open(path, "wb") as f:
                f.write(first_chunk)
                for chunk in gen:
                    f.write(chunk)


def encode_base64url(data: bytes) -> str:
    """
    Encode the input with URL-safe base64 encoding, with no padding.
    """
    return base64.b64encode(data, b"-_").rstrip(b"=").decode("ASCII")


class ClientContainer(DAPContainer):
    def upload(self, task_id: bytes, leader_endpoint: str,
               helper_endpoint: str, vdaf: dict, measurement: str,
               time: Union[int, None], time_precision: int):
        request_body = {
            "task_id": encode_base64url(task_id),
            "leader": leader_endpoint,
            "helper": helper_endpoint,
            "vdaf": vdaf,
            "measurement": measurement,
            "time_precision": time_precision,
        }
        if time is not None:
            request_body["time"] = time
        self.make_request("internal/test/upload", request_body)


class AggregatorContainer(DAPContainer):
    def endpoint_for_task(self, task_id: bytes, role: str):
        request_body = {
            "task_id": encode_base64url(task_id),
            "role": role,
            "hostname": self._container.name,
        }
        response_body = self.make_request(
            "internal/test/endpoint_for_task", request_body)
        raw_endpoint = response_body["endpoint"]
        return urljoin(self.container_base_url(), raw_endpoint)

    def add_task(self, task_id: bytes, role: str,
                 leader_endpoint: str, helper_endpoint: str, vdaf: dict,
                 leader_token: str, collector_token: Union[str, None],
                 verify_key: bytes, max_batch_query_count: int,
                 min_batch_size: int, time_precision: int,
                 collector_hpke_config_base64: str, task_expiration: int):
        request_body = {
            "task_id": encode_base64url(task_id),
            "leader": leader_endpoint,
            "helper": helper_endpoint,
            "vdaf": vdaf,
            "leader_authentication_token": leader_token,
            "role": role,
            "verify_key": encode_base64url(verify_key),
            "max_batch_query_count": max_batch_query_count,
            "query_type": 1,
            "min_batch_size": min_batch_size,
            "time_precision": time_precision,
            "collector_hpke_config": collector_hpke_config_base64,
            "task_expiration": task_expiration,
        }
        if collector_token is not None:
            request_body["collector_authentication_token"] = collector_token
        self.make_request("internal/test/add_task", request_body)


class CollectorContainer(DAPContainer):
    def add_task(self, task_id: bytes, leader_endpoint: str,
                 vdaf: dict, auth_token: str) -> str:
        request_body = {
            "task_id": encode_base64url(task_id),
            "leader": leader_endpoint,
            "vdaf": vdaf,
            "collector_authentication_token": auth_token,
            "query_type": 1,
        }
        response_body = self.make_request(
            "internal/test/add_task", request_body)
        return response_body["collector_hpke_config"]

    def collect_start(self, task_id: bytes, _aggregation_param: None,
                      batch_interval_start: int,
                      batch_interval_duration: int) -> str:
        request_body = {
            "task_id": encode_base64url(task_id),
            "agg_param": "",
            "query": {
                "type": 1,
                "batch_interval_start": batch_interval_start,
                "batch_interval_duration": batch_interval_duration,
            }
        }
        response_body = self.make_request(
            "internal/test/collect_start", request_body)
        return response_body["handle"]

    def collect_poll(self, handle: str) -> Union[str, List[str], None]:
        request_body = {"handle": handle}
        response_body = self.make_request(
            "internal/test/collect_poll", request_body)
        if response_body["status"] == "in progress":
            return None
        else:
            return response_body["result"]


@contextlib.contextmanager
def container_network(client: docker.DockerClient, name: str):
    network = client.networks.create(
        name,
        driver="bridge",
        check_duplicate=True,
    )
    try:
        yield network
    finally:
        network.remove()


@contextlib.contextmanager
def run_container(client: docker.DockerClient, image: str, name: str, network,
                  constructor):
    container = client.containers.run(
        image,
        detach=True,
        name=name,
        network=network.name,
        ports={
            "8080/tcp": None,
        }
    )
    try:
        yield constructor(container, image)
    finally:
        container.remove(force=True)
