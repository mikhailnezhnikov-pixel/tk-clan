#!/usr/bin/env python3
import lzma, hashlib
from pathlib import Path

p=Path("/tmp/full235-attrs2.bin.xz")
raw=lzma.decompress(p.read_bytes())
assert len(raw)==306001
assert hashlib.sha256(raw).hexdigest()=="728d33fbc57105109cd67f3b46de61d27bc2c4c597b9b88012952c0ad3cf0dbf"
print("FULL235_ATTRS2_PROBE_ONLY=PASS")
print("ATTRS2_SIZE=",len(raw))
print("ATTRS2_HEAD_HEX=",raw[:256].hex())
print("ATTRS2_HEAD_REPR=",repr(raw[:256]))
