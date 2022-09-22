import contextlib
import random
import string

from . import containers
from .models import ImageSet, TestCase

IDENTIFIER_ALPHABET = string.ascii_lowercase + string.digits


def run_test(client, image_set: ImageSet, test_case: TestCase):
    random_id = "".join(random.choices(IDENTIFIER_ALPHABET, k=10))
    with contextlib.ExitStack() as stack:
        network = stack.enter_context(
            containers.container_network(client, f"dap-interop-{random_id}")
        )
        client_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.client,
                f"dap-client-{random_id}",
                network,
            )
        )
        leader_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.leader,
                f"dap-leader-{random_id}",
                network,
            )
        )
        helper_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.helper,
                f"dap-helper-{random_id}",
                network,
            )
        )
        collector_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.collector,
                f"dap-collector-{random_id}",
                network,
            )
        )
        all_containers = [client_container, leader_container,
                          helper_container, collector_container]

        for container in all_containers:
            container.wait_for_ready()
