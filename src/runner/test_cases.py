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
        "time_prio3_sum_vec_8_10",
        {
            "type": "Prio3SumVec",
            "bits": "8",
            "length": "10",
            "chunk_length": "12",
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_histogram_5_buckets",
        {
            "type": "Prio3Histogram",
            "length": "5",
            "chunk_length": "2",
        },
        10,
        QueryType.TIME_INTERVAL,
    ),
    TestCase(
        "time_prio3_histogram_12_buckets",
        {
            "type": "Prio3Histogram",
            "length": "12",
            "chunk_length": "4",
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
        "fixed_prio3_sum_vec_8_10",
        {
            "type": "Prio3SumVec",
            "bits": "8",
            "length": "10",
            "chunk_length": "12",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_histogram_5_buckets",
        {
            "type": "Prio3Histogram",
            "length": "5",
            "chunk_length": "2",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
    TestCase(
        "fixed_prio3_histogram_12_buckets",
        {
            "type": "Prio3Histogram",
            "length": "12",
            "chunk_length": "4",
        },
        10,
        QueryType.FIXED_SIZE,
    ),
]
