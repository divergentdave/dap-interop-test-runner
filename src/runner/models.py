from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    TIME_INTERVAL = 1
    FIXED_SIZE = 2


class Query(ABC):
    @property
    @abstractmethod
    def query_type(self) -> QueryType:
        ...

    @abstractmethod
    def to_json(self) -> dict:
        ...


class TimeIntervalQuery(Query):
    def __init__(self,
                 batch_interval_start: int,
                 batch_interval_duration: int):
        self.batch_interval_start = batch_interval_start
        self.batch_interval_duration = batch_interval_duration

    @property
    def query_type(self) -> QueryType:
        return QueryType.TIME_INTERVAL

    def to_json(self) -> dict:
        return {
            "type": self.query_type.value,
            "batch_interval_start": self.batch_interval_start,
            "batch_interval_duration": self.batch_interval_duration,
        }


class FixedSizeQuery(Query):
    def __init__(self):
        pass

    @property
    def query_type(self) -> QueryType:
        return QueryType.FIXED_SIZE

    def to_json(self) -> dict:
        return {
            "type": self.query_type.value,
            # Only the current_batch query subtype is supported for now
            "subtype": 1,
        }


@dataclass(frozen=True)
class TestCase:
    name: str
    vdaf: dict
    measurement_count: int
    query_type: QueryType


@dataclass(frozen=True)
class ImageSet:
    client: str
    leader: str
    helper: str
    collector: str
