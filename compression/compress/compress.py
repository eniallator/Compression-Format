from functools import reduce
from typing import Tuple

from ..exceptions import InconsistentShape, UnexpectedLeaf
from ..types import CompressedList, DataEntry, IntListND


def validate_and_copy(
    data: IntListND,
    shape: Tuple[int] = tuple(),
    shape_idx: int = 0,
    build_shape: bool = True,
) -> Tuple[IntListND, Tuple[int]]:
    data_copy = []
    shape = (*shape, len(data)) if build_shape else shape
    if len(data) != shape[shape_idx]:
        raise InconsistentShape(shape, len(data), shape_idx)
    for item in data:
        if isinstance(item, int):
            if len(shape) != shape_idx + 1:
                raise UnexpectedLeaf(shape, shape_idx)
            data_copy.append(item)
            build_shape = False
        elif isinstance(item, list):
            if len(shape) <= shape_idx:
                raise InconsistentShape(shape, len(item), shape_idx + 1)
            item_copy, item_shape = validate_and_copy(
                item, shape, shape_idx + 1, build_shape
            )
            data_copy.append(item_copy)
            if build_shape:
                shape = item_shape
                build_shape = False
        else:
            raise TypeError(
                f"Expected an N-dimensional list of integers, found {type(item)}"
            )
    return data_copy, shape


def make_path(shape: Tuple[int], index: int) -> tuple[int]:
    path = []
    for n in shape[::-1]:
        path.insert(0, index % n)
        index //= n
    return tuple(path)


def value_at(data: IntListND, path: Tuple[int]) -> int:
    if not path:
        raise IndexError("Invalid data path")
    elif len(path) == 1:
        return data[path[0]]
    else:
        return value_at(data[path[0]], path[1:])


def check_all_same(
    data: IntListND,
    offset_path: Tuple[int],
    next_slice: Tuple[int],
    value: int,
) -> bool:
    if len(next_slice) == 0:
        return True
    if next_slice[0] == 0:
        return check_all_same(
            data[offset_path[0]], offset_path[1:], next_slice[1:], value
        )

    is_leaf = len(next_slice) == 1
    for i in range(offset_path[0], offset_path[0] + next_slice[0]):
        if (is_leaf and data[i] != value) or (
            not is_leaf
            and not check_all_same(data[i], offset_path[1:], next_slice[1:], value)
        ):
            return False
    return True


def calculate_cuboid(
    data: IntListND, shape: Tuple[int], path: Tuple[int], value: int
) -> Tuple[int]:
    lengths = [0] * len(shape)
    for dimension in range(len(shape) - 1, -1, -1):
        next_slice = tuple(1 if i == dimension else n for i, n in enumerate(lengths))
        for _ in range(shape[dimension] - path[dimension]):
            offset_path = tuple(
                p + l if i == dimension else p
                for i, (p, l) in enumerate(zip(path, lengths))
            )
            if check_all_same(data, offset_path, next_slice, value):
                lengths[dimension] += 1
            else:
                break
    return tuple(lengths)


def reset_cuboid(data: IntListND, path: Tuple[int], lengths: Tuple[int]) -> None:
    for i in range(path[0], path[0] + lengths[0]):
        if len(path) == 1:
            data[i] = None
        else:
            reset_cuboid(data[i], path[1:], lengths[1:])


def consume_data_entry(
    data: IntListND, shape: Tuple[int], path: Tuple[int]
) -> DataEntry:
    value = value_at(data, path)

    lengths = calculate_cuboid(data, shape, path, value)

    reset_cuboid(data, path, lengths)

    return DataEntry(value, path, lengths)


def compress(data: IntListND) -> CompressedList:
    """Compresses data into a flattened tuple of DataEntry objects

    Args:
        data (IntListND): Any dimensional List of integers. It must have a consistent shape.

    Returns:
        CompressedList: Compressed version of the data
    """
    data_copy, shape = validate_and_copy(data)

    entries = []
    index = 0
    max_index = reduce(lambda a, b: a * b, shape)
    while index < max_index:
        path = make_path(shape, index)
        if value_at(data_copy, path) == None:
            index += 1
        else:
            data_entry = consume_data_entry(data_copy, shape, path)
            entries.append(data_entry)
            index += data_entry.lengths[-1]

    value_counts = {}
    for entry in entries:
        value_counts[entry.value] = value_counts.get(entry.value, 0) + 1
    default_value = max(value_counts.items(), key=lambda item: item[1])[0]
    filtered_entries = list(filter(lambda entry: entry.value != default_value, entries))

    return CompressedList(shape, default_value, filtered_entries)
