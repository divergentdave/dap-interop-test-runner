import argparse
import collections
import logging
import sys
import traceback

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

import docker  # type: ignore

from . import run_test
from .models import ImageSet
from .test_cases import TEST_CASES


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for DAP interoperation tests")
    parser.add_argument("--image-lists", default="images.toml",
                        help="TOML file with lists of container images. "
                        "Defaults to `images.toml`. Tests will be executed "
                        "with every combination of images from these lists.")
    parser.add_argument("--client", help="Client container image")
    parser.add_argument("--leader", help="Leader container image")
    parser.add_argument("--helper", help="Helper container image")
    parser.add_argument("--collector", help="Collector container image")
    parser.add_argument("--pull", action="store_true",
                        help="Pull updated container images before running")
    parser.add_argument("--list", action="store_true",
                        help="List available test cases")
    parser.add_argument("-v", "--verbose", action="count", help="Verbosity "
                        "level. This may be specified up to three times.")
    parser.add_argument("test_case_filter", metavar="FILTER", nargs="*",
                        help="Filter to select test cases")
    args = parser.parse_args()

    logging.basicConfig()
    if not args.verbose:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose == 1:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose == 2:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        for test_case in TEST_CASES:
            print(test_case.name)
        return

    client = docker.from_env()
    client.ping()

    image_sets = None
    images_to_pull = set()
    if args.client or args.leader or args.helper or args.collector:
        if (not args.client or not args.leader or not args.helper or
                not args.collector):
            print("Either all or none of --client, --leader, --helper, and "
                  "--collector must be provided", file=sys.stderr)
            sys.exit(2)
        image_sets = [ImageSet(args.client, args.leader,
                               args.helper, args.collector)]
        images_to_pull.add(args.client)
        images_to_pull.add(args.leader)
        images_to_pull.add(args.helper)
        images_to_pull.add(args.collector)
    else:
        with open(args.image_lists, "rb") as f:
            images_dict = tomllib.load(f)
        image_sets = list()
        for list_key in ("client", "leader", "helper", "collector"):
            for image in images_dict[list_key]:
                images_to_pull.add(image)
        for client_image in images_dict["client"]:
            for leader_image in images_dict["leader"]:
                for helper_image in images_dict["helper"]:
                    for collector_image in images_dict["collector"]:
                        image_sets.append(ImageSet(
                            client_image,
                            leader_image,
                            helper_image,
                            collector_image,
                        ))

    if args.pull:
        for image in images_to_pull:
            client.images.pull(image)

    filtered_test_cases = []
    for test_case in TEST_CASES:
        matches = False
        if args.test_case_filter:
            for filter in args.test_case_filter:
                if filter in test_case.name:
                    matches = True
                    break
        else:
            matches = True

        if matches:
            filtered_test_cases.append(test_case)

    any_error = False
    success_counters = collections.OrderedDict(
        (image_set, 0) for image_set in image_sets
    )
    for image_set in image_sets:
        for test_case in filtered_test_cases:
            try:
                run_test(client, image_set, test_case)
                print(f"{image_set.client}, {image_set.leader}, "
                      f"{image_set.helper}, {image_set.collector} - "
                      f"{test_case.name}: pass")
                success_counters[image_set] += 1
            except Exception:
                traceback.print_exc()
                print(f"{image_set.client}, {image_set.leader}, "
                      f"{image_set.helper}, {image_set.collector} - "
                      f"{test_case.name}: fail")
                any_error = True
    print()

    if TEST_CASES != filtered_test_cases:
        print(f"Filter selected {len(filtered_test_cases)} out of "
              f"{len(TEST_CASES)} test cases")

    for image_set, success_count in success_counters.items():
        print(f"{image_set.client}, {image_set.leader}, {image_set.helper}, "
              f"{image_set.collector}: {success_count}/"
              f"{len(filtered_test_cases)} passed")

    if any_error:
        print("Files captured from the most recent failed test case have been "
              "saved to the directory ./error_logs/")


if __name__ == "__main__":
    main()
