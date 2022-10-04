This is a reference interoperation test harness, using [ draft-dcook-ppm-dap-interop-test-design-01](https://datatracker.ietf.org/doc/draft-dcook-ppm-dap-interop-test-design/01/), to test [DAP-PPM](https://datatracker.ietf.org/doc/draft-ietf-ppm-dap/) implementations against each other.

## Prerequisites

[Python](https://www.python.org/downloads/) and [Docker](https://www.docker.com/) must be installed. Python versions 3.7, 3.8, 3.9, and 3.10 have been tested. It is strongly recommended to install this package and its dependencies inside a [virtualenv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment).

## Installation

Run the following command to install this package and its dependencies. (If you plan to modify the code, [see below](#development) for how to install the package in editable mode)

```bash
pip install .
```

## Running

By default, the test harness will run all test cases against all available implementations. The file images.toml lists container images available for each DAP role, but presently these images aren't yet published, and must be built from source locally. Container images can also be specified explicitly on the command line, to run test cases against a single combination of implementations.

```bash
# Default options: run all test cases, and test all combinations of images from images.toml.
python -m runner

# Filter test cases, and only run test cases with names that match "histogram".
python -m runner histogram

# List available test cases.
python -m runner --list

# Specify a single combination of container images.
python -m runner --client divviup_ts_interop_client:latest --leader janus_interop_aggregator:latest --helper janus_interop_aggregator:latest --collector janus_interop_collector:latest

# Specify a different set of container images, and test all combinations of its contents.
python -m runner --image-lists my-images.toml

# Pull the container images from their repository, and then run test cases as normal.
python -m runner --pull --client example/dap-client:latest --leader example/dap-aggregator:latest --helper example/dap-aggregator:latest --collector example/dap-collector:latest
```

## Development

To set up a virtualenv for development, run the following command. This will make files in the source tree available for import, so that changes may take effect without reinstalling.

```bash
pip install --editable .
```

Install additional development tools with the following command.

```bash
pip install -r requirements-dev.txt
```
