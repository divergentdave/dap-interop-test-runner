from dataclasses import dataclass


@dataclass
class TestCase:
    name: str
    vdaf: dict
    measurement_count: int


@dataclass
class ImageSet:
    client: str
    leader: str
    helper: str
    collector: str
