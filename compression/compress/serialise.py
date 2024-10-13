from math import ceil, log2
from typing import Dict, List

from ..constants import RESERVED_KEYS, VERSION
from ..types import CompressedList


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


def serialise(compressed_list: CompressedList, metadata: Dict[str, str] = None) -> str:
    """Serialises a CompressedList to binary

    Args:
        compressed_list (CompressedList): Data to serialise
        metadata (Dict[str, str]): Custom metadata to serialise alongside the data. Defaults to None.

    Returns:
        str: Serialised data
    """
    possible_values = sorted(set(entry.value for entry in compressed_list.entries))
    value_lookup = {v: i for i, v in enumerate(possible_values)}
    deltas = [n - p for n, p in zip(possible_values[1:], possible_values[:-1])]

    max_path_sizes = []
    if compressed_list.entries:
        for i in range(len(compressed_list.shape)):
            curr_max_path = max(
                compressed_list.entries, key=lambda entry, i=i: entry.path[i]
            ).path[i]
            max_path_sizes.append(ceil(log2(curr_max_path + 1)))

    # Lengths have to be 1 or greater, so subtracting 1 from each length
    max_length_sizes = []
    if compressed_list.entries:
        for i in range(len(compressed_list.shape)):
            curr_max_length = max(
                compressed_list.entries, key=lambda entry, i=i: entry.lengths[i]
            ).lengths[i]
            if curr_max_length > 0:
                max_length_sizes.append(ceil(log2(curr_max_length)))
            else:
                max_length_sizes.append(0)

    value_bit_length = ceil(log2(len(possible_values) + 1))
    data_bits = "".join(
        (
            pos_int_to_bits(value_lookup[entry.value], value_bit_length)
            if len(possible_values) > 0
            else ""
        )
        + "".join(
            pos_int_to_bits(n, max_path_sizes[i])
            for i, n in enumerate(entry.path)
            if max_path_sizes[i] > 0
        )
        + "".join(
            pos_int_to_bits(n - 1, max_length_sizes[i])
            for i, n in enumerate(entry.lengths)
            if max_length_sizes[i] > 0
        )
        for entry in compressed_list.entries
    )

    # Convert numbers into dynamic int binary
    default_metadata = {
        "VN": pos_int_to_dynamic_bytes(VERSION),
        "DP" if compressed_list.default_value >= 0 else "DN": pos_int_to_dynamic_bytes(
            abs(compressed_list.default_value)
        ),
        "SD": pos_int_list_to_dynamic_bytes(compressed_list.shape),
    }
    if possible_values:
        run_length_offset_deltas = []
        for d in deltas:
            offset = d - 1
            if (
                not run_length_offset_deltas
                or run_length_offset_deltas[-1][1] != offset
            ):
                run_length_offset_deltas.append([0, offset])
            else:
                run_length_offset_deltas[-1][0] += 1
        delta_run_bit_length = ceil(
            log2(max(item[0] for item in run_length_offset_deltas) + 1)
        )
        delta_bit_length = ceil(
            log2(max(item[1] for item in run_length_offset_deltas) + 1)
        )
        delta_bits = "".join(
            (pos_int_to_bits(run, delta_run_bit_length) if run > 0 else "")
            + (pos_int_to_bits(delta, delta_bit_length) if delta > 0 else "")
            for run, delta in run_length_offset_deltas
        )

        default_metadata["MP" if possible_values[0] >= 0 else "MN"] = (
            pos_int_to_dynamic_bytes(abs(possible_values[0]))
        )
        default_metadata["DR"] = pos_int_to_dynamic_bytes(delta_run_bit_length)
        default_metadata["DB"] = pos_int_to_dynamic_bytes(delta_bit_length)
        default_metadata["VD"] = bits_to_bytes(delta_bits)
        default_metadata["RO"] = f"{(8-len(delta_bits)) % 8}"
        default_metadata["DO"] = f"{(8-len(data_bits)) % 8}"
        default_metadata["AS"] = pos_int_list_to_dynamic_bytes(
            max_path_sizes + max_length_sizes
        )

    output_parts = []

    if metadata is not None:
        output_parts.append(
            chr(0).join(
                sanitize(key) + chr(0) + sanitize(metadata[key])
                for key in set(metadata.keys()) - RESERVED_KEYS
            )
        )

    output_parts.append(
        chr(0).join(
            sanitize(key) + chr(0) + sanitize(value)
            for key, value in default_metadata.items()
        )
    )
    if possible_values:
        output_parts.append("CD" + chr(0) + bits_to_bytes(data_bits))

    output = chr(0).join(output_parts)

    return output
