from dataclasses import dataclass


@dataclass(frozen=True)
class TestCase:
    name: str
    vdaf: dict
    measurement_count: int


@dataclass(frozen=True)
class ImageSet:
    client: str
    leader: str
    helper: str
    collector: str
