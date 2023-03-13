from typing import List, Tuple
from math import ceil, log2

from ..types import DataEntry, CompressedList
from ..constants import VERSION, RESERVED_KEYS


def dynamic_bits_to_pos_int(
    dynamic_bits: str, chunk_size: int, i: int = 0
) -> Tuple[int, int]:
    bits = ""
    while i < len(dynamic_bits):
        bits += dynamic_bits[i : i + chunk_size]
        i += chunk_size
        if dynamic_bits[i] == "0":
            break
        i += 1
    return int(bits, base=2), i


def bytes_to_bits(_bytes: str) -> str:
    bits = ""
    for char in _bytes:
        curr_bits = bin(ord(char))[2:]
        bits += (8 - len(curr_bits)) * "0" + curr_bits
    return bits


def dynamic_bytes_to_pos_int(dynamic_bytes: str, num_bytes: int = 1) -> int:
    return dynamic_bits_to_pos_int(bytes_to_bits(dynamic_bytes), num_bytes * 8 - 1)[0]


def dynamic_bytes_to_pos_int_list(
    dynamic_bytes: str, bits_per_item: int = 7
) -> List[int]:
    bits = bytes_to_bits(dynamic_bytes)
    length, i = dynamic_bits_to_pos_int(bits, 7)
    int_list = []
    for _ in range(length):
        item, i = dynamic_bits_to_pos_int(bits, bits_per_item, i + 1)
        int_list.append(item)
    return int_list


def deserialise(serialised: str) -> CompressedList:
    """Deserialises a compressed list that has been previously serialised

    Args:
        serialised (str): Serialised compressed list

    Returns:
        CompressedList: Recovered compressed list object
    """
    i = 0
    curr_item = ""
    wildcard_flag = False
    key = None
    metadata = {}
    while i < len(serialised):
        char = serialised[i]
        i += 1
        if not wildcard_flag and char == chr(1):
            wildcard_flag = True
        elif wildcard_flag:
            curr_item += char
            wildcard_flag = False
        elif char != chr(0):
            curr_item += char
        else:
            # Flush current item
            if key is None:
                key = curr_item
            else:
                metadata[key] = curr_item or chr(0)
                key = None
            curr_item = ""
    metadata[key] = curr_item

    custom_metadata = {
        key: value for key, value in metadata.items() if key not in RESERVED_KEYS
    }

    default_metadata = {}

    default_metadata["VN"] = dynamic_bytes_to_pos_int(metadata["VN"])
    if "MP" in metadata:
        default_metadata["MP"] = dynamic_bytes_to_pos_int(metadata["MP"])
    else:
        default_metadata["MN"] = -dynamic_bytes_to_pos_int(metadata["MN"])

    if "DP" in metadata:
        default_metadata["DP"] = dynamic_bytes_to_pos_int(metadata["DP"])
    else:
        default_metadata["DN"] = -dynamic_bytes_to_pos_int(metadata["DN"])
    default_metadata["SD"] = dynamic_bytes_to_pos_int_list(metadata["SD"])
    default_metadata["VD"] = dynamic_bytes_to_pos_int_list(metadata["VD"])
    default_metadata["AS"] = dynamic_bytes_to_pos_int_list(metadata["AS"])
    default_metadata["DO"] = int(metadata["DO"])

    possible_values = [
        default_metadata["MN"] if "MN" in default_metadata else default_metadata["MP"]
    ]
    for delta in default_metadata["VD"]:
        possible_values.append(possible_values[-1] + delta)

    value_bit_length = ceil(log2(len(possible_values)))
    max_path_sizes = default_metadata["AS"][: len(default_metadata["AS"]) // 2]
    max_length_sizes = default_metadata["AS"][len(default_metadata["AS"]) // 2 :]

    data_bits = bytes_to_bits(metadata["CD"])
    entries = []
    i = 0
    while i < len(data_bits) - default_metadata["DO"]:
        value = (
            possible_values[int(data_bits[i : i + value_bit_length], base=2)]
            if value_bit_length > 0
            else possible_values[0]
        )
        i += value_bit_length
        path = []
        for p in max_path_sizes:
            if p > 0:
                path.append(int(data_bits[i : i + p], base=2))
                i += p
            else:
                path.append(0)
        lengths = []
        for l in max_length_sizes:
            if l > 0:
                lengths.append(int(data_bits[i : i + l], base=2))
                i += l
            else:
                lengths.append(0)
        entries.append(DataEntry(value, path, lengths))

    return CompressedList(
        tuple(default_metadata["SD"]),
        default_metadata["DN"] if "DN" in default_metadata else default_metadata["DP"],
        entries,
        custom_metadata,
    )