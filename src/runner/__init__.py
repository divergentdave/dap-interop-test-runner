import contextlib
import os
import random
import shutil
import string
import time

from . import containers
from .containers import (
    ClientContainer, AggregatorContainer, CollectorContainer,
)
from .dap import generate_auth_token, generate_task_id
from .models import ImageSet, TestCase
from .vdaf import (
    aggregate_measurements, generate_measurement, generate_verify_key,
)

IDENTIFIER_ALPHABET = string.ascii_lowercase + string.digits

LOG_ON_ERROR_DIRECTORY = "error_logs"


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
                ClientContainer,
            )
        )
        leader_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.leader,
                f"dap-leader-{random_id}",
                network,
                AggregatorContainer,
            )
        )
        helper_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.helper,
                f"dap-helper-{random_id}",
                network,
                AggregatorContainer,
            )
        )
        collector_container = stack.enter_context(
            containers.run_container(
                client,
                image_set.collector,
                f"dap-collector-{random_id}",
                network,
                CollectorContainer,
            )
        )

        try:
            run_test_inner(client_container, leader_container,
                           helper_container, collector_container, test_case)
        except Exception:
            shutil.rmtree(LOG_ON_ERROR_DIRECTORY, ignore_errors=True)
            os.mkdir(LOG_ON_ERROR_DIRECTORY)
            for name, container in (("client", client_container),
                                    ("leader", leader_container),
                                    ("helper", helper_container),
                                    ("collector", collector_container)):
                subdirectory = os.path.join(LOG_ON_ERROR_DIRECTORY, name)
                os.mkdir(subdirectory)
                container.copy_logs_directory(subdirectory)
                container.save_process_logs(os.path.join(
                    subdirectory, "container_process.log"))
            raise


def run_test_inner(client_container: ClientContainer,
                   leader_container: AggregatorContainer,
                   helper_container: AggregatorContainer,
                   collector_container: CollectorContainer,
                   test_case: TestCase):
    for container in [client_container, leader_container,
                      helper_container, collector_container]:
        container.wait_for_ready()

    task_id = generate_task_id()
    aggregator_auth_token = generate_auth_token("leader")
    collector_auth_token = generate_auth_token("collector")
    verify_key = generate_verify_key(test_case.vdaf)

    leader_endpoint = leader_container.endpoint_for_task(task_id, 0)
    helper_endpoint = helper_container.endpoint_for_task(task_id, 1)

    collector_hpke_config_base64 = collector_container.add_task(
        task_id,
        leader_endpoint,
        test_case.vdaf,
        collector_auth_token,
    )

    # Fix these task parameters for now
    max_batch_lifetime = 1
    min_batch_size = 1
    min_batch_duration = 3600

    leader_container.add_task(
        task_id,
        0,
        leader_endpoint,
        helper_endpoint,
        test_case.vdaf,
        aggregator_auth_token,
        collector_auth_token,
        verify_key,
        max_batch_lifetime,
        min_batch_size,
        min_batch_duration,
        collector_hpke_config_base64
    )
    helper_container.add_task(
        task_id,
        1,
        leader_endpoint,
        helper_endpoint,
        test_case.vdaf,
        aggregator_auth_token,
        None,
        verify_key,
        max_batch_lifetime,
        min_batch_size,
        min_batch_duration,
        collector_hpke_config_base64
    )

    batch_interval_start = int(
        time.time() // min_batch_duration) * min_batch_duration
    batch_interval_duration = min_batch_duration * 2

    measurements = []
    for _ in range(test_case.measurement_count):
        measurement = generate_measurement(test_case.vdaf)
        measurements.append(measurement)
        client_container.upload(
            task_id,
            leader_endpoint,
            helper_endpoint,
            test_case.vdaf,
            measurement,
            None,
            min_batch_duration,
        )
    expected_aggregate_result = aggregate_measurements(
        test_case.vdaf, None, measurements)

    handle = collector_container.collect_start(
        task_id, None, batch_interval_start, batch_interval_duration)

    result = None
    for _ in range(60):
        result = collector_container.collect_poll(handle)
        if result is not None:
            break
        time.sleep(1)
    else:
        raise Exception("Timed out waiting for collection to complete")

    if expected_aggregate_result != result:
        raise Exception(
            f"Incorrect result, expected {expected_aggregate_result}, "
            f"got {result}")
