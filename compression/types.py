from typing import List, Tuple, NamedTuple


IntListND = List[int] | List["IntListND"]


class DataEntry(NamedTuple):
    value: int
    path: Tuple[int]
    lengths: Tuple[int]


class CompressedList(NamedTuple):
    shape: Tuple[int]
    default_value: int
    entries: List[DataEntry]
