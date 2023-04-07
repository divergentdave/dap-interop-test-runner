from .models import QueryType, TestCase

TEST_CASES = [
    TestCase(
        "time_prio3_count_small",
        {"type": "Prio3Count"},
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_count_medium",
        {"type": "Prio3Count"},
        250,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_count_large",
        {"type": "Prio3Count"},
        5000,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_sum_1_bit",
        {
            "type": "Prio3Sum",
            "bits": "1",
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_sum_8_bits",
        {
            "type": "Prio3Sum",
            "bits": "8",
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_sum_64_bits",
        {
            "type": "Prio3Sum",
            "bits": "64",
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_histogram_5_buckets",
        {
            "type": "Prio3Histogram",
            "buckets": ["1", "3", "10", "30"],
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_histogram_12_buckets",
        {
            "type": "Prio3Histogram",
            "buckets": [
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ],
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "fixed_prio3_count_small",
        {"type": "Prio3Count"},
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_count_medium",
        {"type": "Prio3Count"},
        250,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_count_large",
        {"type": "Prio3Count"},
        5000,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_sum_1_bit",
        {
            "type": "Prio3Sum",
            "bits": "1",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_sum_8_bits",
        {
            "type": "Prio3Sum",
            "bits": "8",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_sum_64_bits",
        {
            "type": "Prio3Sum",
            "bits": "64",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_histogram_5_buckets",
        {
            "type": "Prio3Histogram",
            "buckets": ["1", "3", "10", "30"],
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_histogram_12_buckets",
        {
            "type": "Prio3Histogram",
            "buckets": [
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ],
        },
        10,
        QueryType.FIXED_SIZE,
    ),
]
