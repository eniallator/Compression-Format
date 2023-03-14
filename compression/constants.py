# Bumped whenever the serialisation format changes
VERSION = 1
RESERVED_KEYS = {
    "SD",
    "VN",
    "MP",
    "MN",
    "DP",
    "DN",
    "VD",
    "DB",
    "DR",
    "RO",
    "AS",
    "DO",
    "CD",
}
KEYS_FOR_ENTRIES = {"MP", "MN", "VD", "DB", "DR", "RO", "AS", "DO", "CD"}
# Must have 8 out of the 9 keys above, since MP is present with MN not, and vice versa
MIN_ENTRIES_KEYS = 8
