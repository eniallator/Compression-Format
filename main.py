from compression import (
    compress_to_file,
    decompress_from_file,
)
from functools import reduce


shape = [3, 4, 5]


get_index = lambda path: reduce(
    lambda acc, item: acc * item[0] + item[1], zip(shape, path), 0
)

build_shape = lambda shape, generate_value=lambda n: n, path=[]: [
    generate_value(get_index([*path, i]))
    if len(shape) == 1
    else build_shape(shape[1:], generate_value, [*path, i])
    for i in range(shape[0])
]

data = build_shape(shape, lambda n: 2 * (n // shape[-1] % shape[-2]))

metadata = {"foo": "bar", "hello": "world"}

print(f"Before compression\n{data}\nWith metadata: {metadata}")

compress_to_file("./example.data", data, metadata)
data, metadata = decompress_from_file("./example.data")
print(f"\nAfter decompression\n{data}\nWith metadata: {metadata}")
