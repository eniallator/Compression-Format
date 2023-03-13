from typing import Tuple


class InconsistentShape(Exception):
    def __init__(self, shape: Tuple[int], length: int, shape_idx: int) -> None:
        super().__init__(
            f"Expected shape {shape}, found length {length} at dimension {shape_idx}"
        )


class UnexpectedLeaf(Exception):
    def __init__(self, shape: Tuple[int], shape_idx: int) -> None:
        super().__init__(
            f"Found an unexpected leaf node from shape {shape} at dimension {shape_idx} "
        )
