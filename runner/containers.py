import base64
import contextlib
from urllib.parse import urljoin

import docker  # type: ignore
import requests
import requests.adapters


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


def encode_base64url(data: bytes) -> str:
    """
    Encode the input with URL-safe base64 encoding, with no padding.
    """
    return base64.b64encode(data, b"-_").rstrip(b"=").decode("ASCII")


class ClientContainer(DAPContainer):
    def upload(self, task_id: bytes, leader_endpoint: str,
               helper_endpoint: str, vdaf: dict, measurement: str,
               nonce_time: int | None, min_batch_duration: int):
        request_body = {
            "taskId": encode_base64url(task_id),
            "leader": leader_endpoint,
            "helper": helper_endpoint,
            "vdaf": vdaf,
            "measurement": measurement,
            "minBatchDuration": min_batch_duration,
        }
        if nonce_time is not None:
            request_body["nonceTime"] = nonce_time
        self.make_request("internal/test/upload", request_body)


class AggregatorContainer(DAPContainer):
    def endpoint_for_task(self, task_id: bytes, aggregator_id: int):
        request_body = {
            "taskId": encode_base64url(task_id),
            "aggregatorId": aggregator_id,
            "hostname": self._container.name,
        }
        response_body = self.make_request(
            "internal/test/endpoint_for_task", request_body)
        raw_endpoint = response_body["endpoint"]
        return urljoin(self.container_base_url(), raw_endpoint)

    def add_task(self, task_id: bytes, aggregator_id: int,
                 leader_endpoint: str, helper_endpoint: str, vdaf: dict,
                 leader_token: str, collector_token: str | None,
                 verify_key: bytes, max_batch_lifetime: int,
                 min_batch_size: int, min_batch_duration: int,
                 collector_hpke_config_base64: str):
        request_body = {
            "taskId": encode_base64url(task_id),
            "leader": leader_endpoint,
            "helper": helper_endpoint,
            "vdaf": vdaf,
            "leaderAuthenticationToken": leader_token,
            "aggregatorId": aggregator_id,
            "verifyKey": encode_base64url(verify_key),
            "maxBatchLifetime": max_batch_lifetime,
            "minBatchSize": min_batch_size,
            "minBatchDuration": min_batch_duration,
            "collectorHpkeConfig": collector_hpke_config_base64,
        }
        if collector_token is not None:
            request_body["collectorAuthenticationToken"] = collector_token
        self.make_request("internal/test/add_task", request_body)


class CollectorContainer(DAPContainer):
    def add_task(self, task_id: bytes, leader_endpoint: str, vdaf: dict,
                 auth_token: str) -> str:
        request_body = {
            "taskId": encode_base64url(task_id),
            "leader": leader_endpoint,
            "vdaf": vdaf,
            "collectorAuthenticationToken": auth_token,
        }
        response_body = self.make_request(
            "internal/test/add_task", request_body)
        return response_body["collectorHpkeConfig"]

    def collect_start(self, task_id: bytes, _aggregation_param: None,
                      batch_interval_start: int,
                      batch_interval_duration: int) -> str:
        request_body = {
            "taskId": encode_base64url(task_id),
            "aggParam": "",
            "batchIntervalStart": batch_interval_start,
            "batchIntervalDuration": batch_interval_duration,
        }
        response_body = self.make_request(
            "internal/test/collect_start", request_body)
        return response_body["handle"]

    def collect_poll(self, handle: str) -> str | list[str] | None:
        request_body = {"handle": handle}
        response_body = self.make_request(
            "internal/test/collect_poll", request_body)
        if response_body["status"] == "in progress":
            return None
        else:
            return response_body["result"]


@ contextlib.contextmanager
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
