from functools import reduce

from compression import compress, decompress, deserialise, serialise, compress_to_file

shape = [3, 4, 5]


get_index = lambda path: reduce(
    lambda acc, item: acc * item[0] + item[1], zip(shape, path), 0
)

build_shape = lambda shape, value_fn=lambda n: n, path=[]: [
    (
        value_fn(get_index([*path, i]))
        if len(shape) == 1
        else build_shape(shape[1:], value_fn, [*path, i])
    )
    for i in range(shape[0])
]

data = build_shape(shape, lambda n: 2 * (n // shape[-1] % shape[-2]))
metadata = {"foo": "bar baz", "hello world!": "this is a test"}

compress_to_file("./example.data", data, metadata)

print(f"Before compression\n{data}\nWith metadata: {metadata}")

compressed = compress(data)
print("\nCompressed:")
print(compressed)

serialised = serialise(compressed, metadata)
print(f"\nSerialised (num bytes: {len(serialised.encode('utf-8'))}):")
print(serialised)

deserialised, deserialised_metadata = deserialise(serialised)
print(f"\nDeserialised (metadata found: {deserialised_metadata}):")
print(deserialised)

decompressed = decompress(deserialised)
print("\nDecompressed:")
print(decompressed)
