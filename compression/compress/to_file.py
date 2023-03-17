from typing import Dict, List

from ..types import Data
from .compress import compress
from .serialise import serialise


def compress_to_file(
    file_path: str, data: List[Data], metadata: Dict[str, str] = None
) -> None:
    """Compresses data to a file

    Args:
        file_path (str): File to write
        data (List[Data]): N dimensional list of integers to compress. Must have a consistent shape.
        metadata (Dict[str, str], optional): Any custom metadata to save alongside the data. Defaults to None.
    """
    with open(file_path, "wb") as file_handle:
        file_handle.write(serialise(compress(data), metadata).encode("utf-8"))
