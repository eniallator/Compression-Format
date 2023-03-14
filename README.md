# Compression Format

Takes in an N-dimensional list of numbers, then compresses it, and then finally serialises it into a binary file.
Decompression is just the reverse of the above.

## Compression Strategy

- It takes in an N dimensional list of integers, that has to have a consistent shape.
- Then it will try to partition the integers up into the largest cuboid it can find (greedy approach) of the same values and stores the positions and lengths of each dimension for the cuboid
  - For example, for the following list:

```py
[
  [0,0,0,0,1],
  [0,0,0,0,0],
  [0,0,0,0,0],
  [0,0,0,0,0],
  [0,0,0,0,0],
]
```

- It will find there is a cuboid of value `0` starting from `[0, 0]` with lengths `[5, 4]` (it's not `[5, 5]` since there's a `1` blocking it in the top right there)
  - Then the rest of the entries would be:
    - `value: 1, path: [0, 4], lengths: [1, 1]`
    - `value: 0, path: [1, 4], lengths: [4, 1]`
- Then once this has been done, it will filter out the most common value from the data entries, and then make that the default data value

## Metadata

- Has type `Dict[str, str]`
- Separator is a null byte (`8 * "0"`)
- Any null bytes found in the keys/values have a wildcard in front of them (`7 * "0" + "1"`)
- Any wildcard bytes found in the keys/values have another wildcard byte in front to ignore the wildcard and treat it as a character

### Special Metadata Key/Value Pairs

- All special metadata keys will overwrite any pairs with the same keys found in the given metadata, as these are fundamental for the compression format to work
- Complete list:

| Key | Description                                                                             |
| --- | --------------------------------------------------------------------------------------- |
| VN  | Version number of format                                                                |
| MP  | Minimum value of original data. Only included if it's positive                          |
| MN  | Minimum value of original data. Only included if it's negative                          |
| DP  | Default value of original data. Only included if it's positive                          |
| DN  | Default value of original data. Only included if it's negative                          |
| SD  | Shape of original data                                                                  |
| VD  | Deltas between adjacent values in the sorted list of values that are run length encoded |
| DB  | Delta bit length                                                                        |
| DR  | Delta run bit length                                                                    |
| RO  | Delta offset from the end byte                                                          |
| AS  | Bits per attribute                                                                      |
| DO  | Data offset from the end byte                                                           |
| CD  | Compressed Data (always appears at the end of the metadata)                             |

## Further Optimisations

- Since lengths have to be 1 or greater, I have chosen to subtract 1 from them, so that if there is only a max length of 1, there won't be any bits allocated to it in the compressed data, and it's defaulted to 1 in deserialisation
- Deltas have also been run length encoded
