import hashlib
import json
from pathlib import Path

root = Path("data/test")
hashes = json.loads((root / "label_hashes.json").read_text(encoding="utf-8"))
labels = root / "labels"
for name, expected in hashes.items():
    p = labels / name
    raw = p.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = b"\r\n".join(raw.replace(b"\r\n", b"\n").split(b"\n"))
    if raw.endswith(b"\n") or raw.endswith(b"\r\n"):
        pass
    print(
        name,
        "match",
        got == expected,
        "has_crlf",
        b"\r\n" in raw,
        "lf_match",
        hashlib.sha256(lf).hexdigest() == expected,
        "len",
        len(raw),
        "nlines",
        raw.count(b"\n"),
    )
