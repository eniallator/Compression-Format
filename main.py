from compression import compress, serialise, deserialise, decompress
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

print("Raw Data:")
print(data)

compressed = compress(data, {"foo": "bar", "hello": "world"})
print("Compressed:")
print(compressed)

serialised = serialise(compressed)
print("\nSerialised:")
print(serialised)

deserialised = deserialise(serialised)
print("\nDeserialised:")
print(deserialised)

decompressed, metadata = decompress(deserialised)
print("\nDecompressed:")
print(decompressed)
