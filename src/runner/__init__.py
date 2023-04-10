import contextlib
import datetime
import os
import random
import shutil
import string
import time
import traceback

from . import containers
from .containers import (
    ClientContainer, AggregatorContainer, CollectorContainer, InteropAPIError,
)
from .dap import generate_auth_token, generate_task_id
from .models import (
    FixedSizeQuery, ImageSet, Query, QueryType, TestCase, TimeIntervalQuery,
)
from .vdaf import (
    aggregate_measurements, generate_measurement, generate_vdaf_verify_key,
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
                try:
                    container.copy_logs_directory(subdirectory)
                except Exception:
                    traceback.print_exc()
                    print("Error copying directory from container")
                    print()
                try:
                    container.save_process_logs(os.path.join(
                        subdirectory, "container_process.log"))
                except Exception:
                    traceback.print_exc()
                    print("Error saving container logs")
                    print()
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
    vdaf_verify_key = generate_vdaf_verify_key(test_case.vdaf)

    leader_endpoint = leader_container.endpoint_for_task(task_id, "leader")
    helper_endpoint = helper_container.endpoint_for_task(task_id, "helper")

    collector_hpke_config_base64 = collector_container.add_task(
        task_id,
        leader_endpoint,
        test_case.vdaf,
        collector_auth_token,
        test_case.query_type,
    )

    # Fix these task parameters for now
    max_batch_query_count = 1
    min_batch_size = test_case.measurement_count
    time_precision = 3600
    task_expiration = int(datetime.datetime(3000, 1, 1, 0, 0, 0).timestamp())

    leader_container.add_task(
        task_id,
        "leader",
        leader_endpoint,
        helper_endpoint,
        test_case.vdaf,
        aggregator_auth_token,
        collector_auth_token,
        vdaf_verify_key,
        max_batch_query_count,
        min_batch_size,
        time_precision,
        collector_hpke_config_base64,
        task_expiration,
        test_case.query_type,
    )
    helper_container.add_task(
        task_id,
        "helper",
        leader_endpoint,
        helper_endpoint,
        test_case.vdaf,
        aggregator_auth_token,
        None,
        vdaf_verify_key,
        max_batch_query_count,
        min_batch_size,
        time_precision,
        collector_hpke_config_base64,
        task_expiration,
        test_case.query_type,
    )

    batch_interval_start = int(
        time.time() // time_precision) * time_precision
    batch_interval_duration = time_precision * 2

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
            time_precision,
        )
    expected_aggregate_result = aggregate_measurements(
        test_case.vdaf, None, measurements)

    query: Query
    if test_case.query_type == QueryType.TIME_INTERVAL:
        query = TimeIntervalQuery(
            batch_interval_start,
            batch_interval_duration,
        )
    elif test_case.query_type == QueryType.FIXED_SIZE:
        query = FixedSizeQuery()

    result = None
    for _ in range(5):
        if result is not None:
            break
        try:
            handle = collector_container.collection_start(task_id, None, query)

            for _ in range(30):
                result = collector_container.collection_poll(handle)
                if result is not None:
                    break
                time.sleep(1)
            else:
                raise Exception("Timed out waiting for collection to complete")

        except InteropAPIError:
            time.sleep(1)
            continue
    else:
        raise Exception("Timed out waiting for collection flow")

    if expected_aggregate_result != result:
        raise Exception(
            f"Incorrect result, expected {expected_aggregate_result}, "
            f"got {result}")
