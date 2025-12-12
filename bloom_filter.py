import math
import hashlib
from collections import defaultdict
from typing import Any


class BloomFilter:
    def __init__(self, expected_items: int, false_positive_rate: float):
        self.size = int(-(expected_items * math.log(false_positive_rate)) / (math.log(2) ** 2))
        self.hash_count = int((self.size / expected_items) * math.log(2))
        self.bit_array = defaultdict(bool)
        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate

    def _get_hashes(self, item: Any):
        item_str = str(item).encode("utf-8")
        h1 = int(hashlib.sha256(item_str).hexdigest(), 16)
        h2 = int(hashlib.md5(item_str).hexdigest(), 16)

        for i in range(self.hash_count):
            yield (h1 + i * h2) % self.size

    def add(self, item: Any):
        for hash_index in self._get_hashes(item):
            self.bit_array[hash_index] = True

    def check(self, item: Any) -> bool:
        for hash_index in self._get_hashes(item):
            if not self.bit_array[hash_index]:
                return False
        return True

    def __len__(self):
        return len(self.bit_array)

    def get_stats(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "hash_count": self.hash_count,
            "bits_set": len(self.bit_array),
            "expected_items": self.expected_items,
            "false_positive_rate": self.false_positive_rate,
        }

