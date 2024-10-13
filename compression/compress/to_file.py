from typing import Dict

from ..types import IntListND
from .compress import compress
from .serialise import serialise


def compress_to_file(
    file_path: str, data: IntListND, metadata: Dict[str, str] = None
) -> None:
    """Compresses data to a file

    Args:
        file_path (str): File to write
        data (IntListND): N dimensional list of integers to compress. Must have a consistent shape.
        metadata (Dict[str, str], optional): Any custom metadata to save alongside the data. Defaults to None.
    """
    with open(file_path, "wb") as file_handle:
        file_handle.write(serialise(compress(data), metadata).encode("utf-8"))
