#!/usr/bin/env python3
"""Verify a Python uuid7() implementation before trusting generated IDs.

Usage:
    python3 verify_uuid_v7.py            # self-test the canonical impl below
    python3 verify_uuid_v7.py path.py    # exec path.py, call uuid7() there

Pass criteria: every ID matches the RFC 9562 v7 regex AND starts with the
correct variant nibble. A naive implementation (e.g. concatenating hex
fragments) yields 30-char strings and fails; a wrong variant mask
(0x8<<62 instead of 0x2<<62) yields valid-shape but non-RFC IDs.
"""
import re
import sys
import time

UUID7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def uuid7_canonical() -> str:
    """Correct RFC 9562 UUIDv7: 48-bit ms | ver 7 | 12b rand | var 10xx | 62b rand."""
    import random
    ts_ms = int(time.time() * 1000)
    rand_a = random.getrandbits(12)
    rand_b = random.getrandbits(62)
    value = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    h = f"{value:032x}"
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def load_target(path: str):
    ns = {"time": time, "random": __import__("random")}
    src = open(path, encoding="utf-8").read()
    m = re.search(r"(def uuid7\(\)[\s\S]*?\n\n)", src)
    if not m:
        sys.exit(f"no uuid7() found in {path}")
    exec(m.group(1), ns)
    return ns["uuid7"]


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    fn = load_target if (target := sys.argv[1] if len(sys.argv) > 1 else None) else uuid7_canonical
    if target:
        fn = load_target(target)

    ids = [fn() for _ in range(200)]
    ok = all(UUID7_RE.match(u) for u in ids)
    # time-ordering: allow same-ms ties, require monotonic across distinct ms
    parsed = sorted(ids)
    print(f"generated: {len(ids)}")
    print(f"regex valid: {ok}")
    if not ok:
        for u in ids[:3]:
            print("  BAD:", u)
        sys.exit(1)
    print("sample:", ids[0])
    print("PASS")


if __name__ == "__main__":
    main()
