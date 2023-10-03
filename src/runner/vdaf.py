import random
import secrets
from typing import List, Union


def generate_measurement(vdaf_dict: dict) -> Union[str, List[str]]:
    """
    Randomly generate a valid measurement for the given VDAF.
    """
    vdaf_type = vdaf_dict["type"]
    if vdaf_type == "Prio3Count":
        return str(random.randint(0, 1))
    elif vdaf_type == "Prio3Sum":
        bits = int(vdaf_dict["bits"])
        return str(random.randrange(0, 1 << bits))
    elif vdaf_type == "Prio3SumVec":
        length = int(vdaf_dict["length"])
        bits = int(vdaf_dict["bits"])
        limit = 1 << bits
        return [str(random.randrange(0, limit)) for _ in range(length)]
    elif vdaf_type == "Prio3Histogram":
        length = int(vdaf_dict["length"])
        return str(random.randrange(0, length))
    else:
        raise Exception(f"Unsupported VDAF: {vdaf_type}")


def aggregate_measurements(vdaf_dict: dict, _aggregation_param: None,
                           measurements: List[Union[str, List[str]]]
                           ) -> Union[str, List[str]]:
    """
    Compute the expected aggregate result from running a VDAF over a list of
    measurements with a given aggregation parameter.
    """
    vdaf_type = vdaf_dict["type"]
    if vdaf_type == "Prio3Count":
        total = 0
        for measurement in measurements:
            assert isinstance(measurement, str)
            total += int(measurement)
        return str(total)
    elif vdaf_type == "Prio3Sum":
        total = 0
        for measurement in measurements:
            assert isinstance(measurement, str)
            total += int(measurement)
        return str(total)
    elif vdaf_type == "Prio3SumVec":
        length = int(vdaf_dict["length"])
        totals = [0] * length
        for measurement in measurements:
            for i, value in enumerate(measurement):
                assert isinstance(value, str)
                totals[i] += int(value)
        return [str(value) for value in totals]
    elif vdaf_type == "Prio3Histogram":
        length = int(vdaf_dict["length"])
        totals = [0] * length
        for measurement in measurements:
            assert isinstance(measurement, str)
            totals[int(measurement)] += 1
        return [str(value) for value in totals]
    raise Exception(f"Unsupported VDAF: {vdaf_type}")


def generate_vdaf_verify_key(vdaf_dict: dict) -> bytes:
    """Generate a verification key for a VDAF"""
    vdaf_type = vdaf_dict["type"]
    if vdaf_type in ("Prio3Count", "Prio3Sum",
                     "Prio3SumVec", "Prio3Histogram"):
        return secrets.token_bytes(16)
    else:
        raise Exception(f"Unsupported VDAF: {vdaf_type}")
