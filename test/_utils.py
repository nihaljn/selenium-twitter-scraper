from typing import Any

class Difference:
    def __init__(self, key: str, expected: Any, actual: Any):
        self.key = key
        self.expected = expected
        self.actual = actual

    def __str__(self):
        # pretty print
        out = "=" * 20 + " " + self.key + " " + "=" * 20
        out += "\n" + "EXPECTED:\n" + str(self.expected)
        out += "\n" + "-" * 50
        out += "\n" + "ACTUAL:\n" + str(self.actual)
        out += "\n"
        return out
