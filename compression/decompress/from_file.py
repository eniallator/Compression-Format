from typing import Dict, List, Tuple

from ..types import Data
from .decompress import decompress
from .deserialise import deserialise


def decompress_from_file(file_path: str) -> Tuple[List[Data], Dict[str, str]]:
    """Reads in a file and deserialises/decompresses the data inside

    Args:
        file_path (str): File to read

    Returns:
        Tuple[List[Data], Dict[str, str]]: The decompressed data followed by any custom metadata
    """
    with open(file_path, "rb") as file_handle:
        compressed_list, metadata = deserialise(file_handle.read().decode("utf-8"))
        return decompress(compressed_list), metadata
