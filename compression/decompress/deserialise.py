from math import ceil, log2
from typing import Dict, List, Tuple

from ..constants import KEYS_FOR_ENTRIES, MIN_ENTRIES_KEYS, RESERVED_KEYS, VERSION
from ..exceptions import VersionMisMatch
from ..types import CompressedList, DataEntry


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


def deserialise(serialised: str) -> Tuple[CompressedList, Dict[str, str]]:
    """Deserialises a compressed list that has been previously serialised

    Args:
        serialised (str): Serialised compressed list

    Returns:
        Tuple[CompressedList, Dict[str,str]]: Deserialised compressed list object followed by any custom metadata found
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
                if curr_item == "CD":
                    key = "CD"
                    curr_item = serialised[i:]
                    break
                else:
                    key = curr_item
                    curr_item = ""
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

    if default_metadata["VN"] != VERSION:
        raise VersionMisMatch(default_metadata["VN"])

    if "DP" in metadata:
        default_metadata["DP"] = dynamic_bytes_to_pos_int(metadata["DP"])
    else:
        default_metadata["DN"] = -dynamic_bytes_to_pos_int(metadata["DN"])
    default_metadata["SD"] = dynamic_bytes_to_pos_int_list(metadata["SD"])

    entries = []
    entries_keys_score = sum(int(key in metadata) for key in KEYS_FOR_ENTRIES)
    if entries_keys_score == MIN_ENTRIES_KEYS:
        if "MP" in metadata:
            default_metadata["MP"] = dynamic_bytes_to_pos_int(metadata["MP"])
        else:
            default_metadata["MN"] = -dynamic_bytes_to_pos_int(metadata["MN"])
        default_metadata["RO"] = int(metadata["RO"])
        default_metadata["DB"] = dynamic_bytes_to_pos_int(metadata["DB"])
        default_metadata["DR"] = dynamic_bytes_to_pos_int(metadata["DR"])

        delta_bits = bytes_to_bits(metadata["VD"])
        run_length_offset_deltas = []
        i = 0
        while i < len(delta_bits) - default_metadata["RO"]:
            item = []

            if default_metadata["DR"] > 0:
                item.append(int(delta_bits[i : i + default_metadata["DR"]], base=2))
                i += default_metadata["DR"]
            else:
                item.append(0)

            if default_metadata["DB"] > 0:
                item.append(int(delta_bits[i : i + default_metadata["DB"]], base=2))
                i += default_metadata["DB"]
            else:
                item.append(0)

            run_length_offset_deltas.append(item)

        deltas = []
        for offset_run, offset_delta in run_length_offset_deltas:
            deltas.extend(offset_delta + 1 for _ in range(offset_run + 1))

        default_metadata["DO"] = int(metadata["DO"])
        default_metadata["AS"] = dynamic_bytes_to_pos_int_list(metadata["AS"])
        possible_values = [
            (
                default_metadata["MN"]
                if "MN" in default_metadata
                else default_metadata["MP"]
            )
        ]
        for delta in deltas:
            possible_values.append(possible_values[-1] + delta)

        value_bit_length = ceil(log2(len(possible_values) + 1))
        max_path_sizes = default_metadata["AS"][: len(default_metadata["AS"]) // 2]
        max_length_sizes = default_metadata["AS"][len(default_metadata["AS"]) // 2 :]

        data_bits = bytes_to_bits(metadata["CD"])
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
                # Lengths have to be 1 or greater, so adding 1 to each length, undoing the subtraction in serialisation
                if l > 0:
                    lengths.append(int(data_bits[i : i + l], base=2) + 1)
                    i += l
                else:
                    lengths.append(1)
            entries.append(DataEntry(value, path, lengths))

    return (
        CompressedList(
            tuple(default_metadata["SD"]),
            (
                default_metadata["DN"]
                if "DN" in default_metadata
                else default_metadata["DP"]
            ),
            entries,
        ),
        custom_metadata or None,
    )
