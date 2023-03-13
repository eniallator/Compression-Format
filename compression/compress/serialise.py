from typing import Dict, List
from math import ceil, log2

from .compress import compress
from ..types import Data, CompressedList
from ..constants import VERSION, RESERVED_KEYS


def pos_int_to_bits(n: int, length: int) -> str:
    bits = bin(n)[2:]
    return (length - len(bits)) * "0" + bits


def pos_int_to_dynamic_bits(n: int, chunk_size: int) -> str:
    bits = bin(n)[2:]
    padded = "0" * (chunk_size - len(bits) % chunk_size) + bits
    return (
        "1".join(
            padded[i * chunk_size : (i + 1) * chunk_size]
            for i in range(len(padded) // chunk_size)
        )
        + "0"
    )


def bits_to_bytes(bits: str) -> str:
    converted = ""
    for i in range(ceil(len(bits) / 8)):
        converted += chr(
            sum(int(b) * 2 ** (7 - j) for j, b in enumerate(bits[i * 8 : (i + 1) * 8]))
        )
    return converted


def pos_int_to_dynamic_bytes(n: int, num_bytes: int = 1) -> str:
    return bits_to_bytes(pos_int_to_dynamic_bits(n, num_bytes * 8 - 1))


def pos_int_list_to_dynamic_bytes(int_list: List[int], bits_per_item: int = 7) -> str:
    return pos_int_to_dynamic_bytes(len(int_list), 1) + bits_to_bytes(
        "".join(pos_int_to_dynamic_bits(n, bits_per_item) for n in int_list)
    )


def sanitize(s: str) -> str:
    return s.replace(chr(1), chr(1) + chr(1)).replace(chr(0), chr(1) + chr(0))


def serialise(compressed_list: CompressedList) -> str:
    """Serialises a CompressedList to binary

    Args:
        compressed_list (CompressedList): Data to serialise

    Returns:
        str: Serialised data
    """
    possible_values = sorted(set(entry.value for entry in compressed_list.entries))
    value_lookup = {v: i for i, v in enumerate(possible_values)}
    deltas = [n - p for n, p in zip(possible_values[1:], possible_values[:-1])]
    max_path_sizes = [
        ceil(
            log2(
                max(compressed_list.entries, key=lambda entry, i=i: entry.path[i]).path[
                    i
                ]
                + 1
            )
        )
        for i in range(len(compressed_list.shape))
    ]
    max_length_sizes = [
        ceil(
            log2(
                max(
                    compressed_list.entries, key=lambda entry, i=i: entry.lengths[i]
                ).lengths[i]
                + 1
            )
        )
        for i in range(len(compressed_list.shape))
    ]

    value_bit_length = ceil(log2(len(possible_values)))
    entries_bits = "".join(
        (
            pos_int_to_bits(value_lookup[entry.value], value_bit_length)
            if len(possible_values) > 1
            else ""
        )
        + "".join(
            pos_int_to_bits(n, max_path_sizes[i])
            for i, n in enumerate(entry.path)
            if max_path_sizes[i] > 0
        )
        + "".join(
            pos_int_to_bits(n, max_length_sizes[i])
            for i, n in enumerate(entry.lengths)
            if max_length_sizes[i] > 0
        )
        for entry in compressed_list.entries
    )

    # Convert numbers into dynamic int binary
    default_metadata = {
        "VN": pos_int_to_dynamic_bytes(VERSION),
        "MP"
        if possible_values[0] >= 0
        else "MN": pos_int_to_dynamic_bytes(abs(possible_values[0])),
        "DP"
        if compressed_list.default_value >= 0
        else "DN": pos_int_to_dynamic_bytes(abs(compressed_list.default_value)),
        "SD": pos_int_list_to_dynamic_bytes(compressed_list.shape),
        "VD": pos_int_list_to_dynamic_bytes(deltas),
        "AS": pos_int_list_to_dynamic_bytes(max_path_sizes + max_length_sizes),
        "DO": f"{len(entries_bits) % 8}",
    }

    output_parts = []

    if compressed_list.metadata:
        output_parts.append(
            chr(0).join(
                sanitize(key) + chr(0) + sanitize(compressed_list.metadata[key])
                for key in set(compressed_list.metadata.keys()) - RESERVED_KEYS
            )
        )

    output_parts.append(
        chr(0).join(
            sanitize(key) + chr(0) + sanitize(value)
            for key, value in default_metadata.items()
        )
    )
    output_parts.append("CD" + chr(0) + bits_to_bytes(entries_bits))

    output = chr(0).join(output_parts)

    return output
