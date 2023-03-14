from typing import Dict, List, Tuple, NamedTuple


Data = int | List["Data"]


class DataEntry(NamedTuple):
    value: int
    path: Tuple[int]
    lengths: Tuple[int]


class CompressedList(NamedTuple):
    shape: Tuple[int]
    default_value: int
    entries: List[DataEntry]
