import random
import secrets
from typing import List, Union


def generate_measurement(vdaf_dict: dict) -> str:
    """
    Randomly generate a valid measurement for the given VDAF.
    """
    vdaf_type = vdaf_dict["type"]
    if vdaf_type == "Prio3Count":
        return str(random.randint(0, 1))
    elif vdaf_type == "Prio3Sum":
        bits = int(vdaf_dict["bits"])
        return str(random.randrange(0, 1 << bits))
    elif vdaf_type == "Prio3Histogram":
        # Each bucket, except for those on the ends, is a left-open,
        # right-closed interval between bucket boundaries.
        buckets = [int(boundary) for boundary in vdaf_dict["buckets"]]
        # Uniformly pick a bucket, and then pick an input that will contribute
        # to that bucket.
        which = random.randint(0, len(buckets))
        if which == 0:
            # Between negative infinity and the first bucket boundary.
            lower_bound = max(0, buckets[0] - 100)
            return str(random.randint(lower_bound, buckets[0]))
        elif which == len(buckets):
            # Between the last bucket boundary and positive infinity.
            return str(random.randint(buckets[-1] + 1, buckets[-1] + 100))
        else:
            # Between two bucket boundaries.
            return str(random.randint(buckets[which - 1] + 1, buckets[which]))
    else:
        raise Exception(f"Unsupported VDAF: {vdaf_type}")


def aggregate_measurements(vdaf_dict: dict, _aggregation_param: None,
                           measurements: List[str]) -> Union[str, List[str]]:
    """
    Compute the expected aggregate result from running a VDAF over a list of
    measurements with a given aggregation parameter.
    """
    vdaf_type = vdaf_dict["type"]
    if vdaf_type == "Prio3Count":
        return str(sum(int(measurement) for measurement in measurements))
    elif vdaf_type == "Prio3Sum":
        return str(sum(int(measurement) for measurement in measurements))
    elif vdaf_type == "Prio3Histogram":
        buckets = [int(boundary) for boundary in vdaf_dict["buckets"]]
        counts = [0] * (len(buckets) + 1)
        for measurement in measurements:
            value = int(measurement)
            for i, bucket in enumerate(buckets):
                if value <= bucket:
                    counts[i] += 1
                    break
            else:
                counts[-1] += 1
        return [str(count) for count in counts]
    raise Exception(f"Unsupported VDAF: {vdaf_type}")


def generate_vdaf_verify_key(vdaf_dict: dict) -> bytes:
    """Generate a verification key for a VDAF"""
    vdaf_type = vdaf_dict["type"]
    if vdaf_type in ("Prio3Count", "Prio3Sum",
                     "Prio3Histogram"):
        return secrets.token_bytes(16)
    else:
        raise Exception(f"Unsupported VDAF: {vdaf_type}")
