import contextlib

import docker  # type: ignore
import requests
import requests.adapters


class DAPContainer:
    def __init__(self, container):
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

    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port()}/"

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
        url = f"{self.base_url()}internal/test/ready"
        response = session.post(url)
        if response.status_code == 200:
            return
        else:
            raise Exception(
                f"Container {self._container.image.tags} replied to "
                "/internal/test/ready with a status code of "
                f"{response.status_code}"
            )


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
def run_container(client: docker.DockerClient, image: str, name: str, network):
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
        yield DAPContainer(container)
    finally:
        container.remove(force=True)
