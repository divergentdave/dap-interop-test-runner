from .models import TestCase

TEST_CASES = [
    TestCase("prio3_count_small", {"type": "Prio3Aes128Count"}, 10),
    TestCase("prio3_count_medium", {"type": "Prio3Aes128Count"}, 250),
    # The large test is commented out for now because Janus can't handle the
    # high throughput without failing some aggregation jobs.
    # TestCase("prio3_count_large", {"type": "Prio3Aes128Count"}, 5000),
    TestCase("prio3_sum_1_bit", {"type": "Prio3Aes128Sum", "bits": "1"}, 10),
    TestCase("prio3_sum_8_bits", {"type": "Prio3Aes128Sum", "bits": "8"}, 10),
    TestCase(
        "prio3_sum_64_bits",
        {
            "type": "Prio3Aes128Sum",
            "bits": "64",
        },
        10,
    ),
    TestCase(
        "prio3_histogram_5_buckets",
        {
            "type": "Prio3Aes128Histogram",
            "buckets": ["1", "3", "10", "30"],
        },
        10,
    ),
    TestCase(
        "prio3_histogram_12_buckets",
        {
            "type": "Prio3Aes128Histogram",
            "buckets": [
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ],
        },
        10,
    ),
]
