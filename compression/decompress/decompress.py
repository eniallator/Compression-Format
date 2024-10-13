from typing import List, Tuple

from ..types import CompressedList, IntListND


def build_shape(shape: Tuple[int], default_value: int) -> IntListND:
    return [
        (default_value if len(shape) == 1 else build_shape(shape[1:], default_value))
        for _ in range(shape[0])
    ]


def set_data_entry(
    data: IntListND, value: int, path: List[int], lengths: List[int]
) -> None:
    for i in range(path[0], path[0] + lengths[0]):
        if len(path) == 1:
            data[i] = value
        else:
            set_data_entry(data[i], value, path[1:], lengths[1:])


def decompress(compressed_list: CompressedList) -> IntListND:
    """Decompresses a compressed list to give the original data/metadata back

    Args:
        compressed_list (CompressedList): Compressed data

    Returns:
        IntListND: Original data
    """
    data = build_shape(compressed_list.shape, compressed_list.default_value)

    for entry in compressed_list.entries:
        set_data_entry(data, entry.value, entry.path, entry.lengths)

    return data
