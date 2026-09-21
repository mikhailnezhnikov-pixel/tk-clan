#!/usr/bin/env python3
import lzma, hashlib
from pathlib import Path
raw=lzma.decompress(Path("/tmp/full235-attrs2.bin.xz").read_bytes())
assert len(raw)==306001
assert hashlib.sha256(raw).hexdigest()=="728d33fbc57105109cd67f3b46de61d27bc2c4c597b9b88012952c0ad3cf0dbf"
print("FULL235_ATTRS2_PROBE_ONLY=PASS")
print("ATTRS2_SIZE=",len(raw))
print("ATTRS2_DATA_WINDOW_HEX=",raw[780:900].hex())
print("ATTRS2_DATA_WINDOW_REPR=",repr(raw[780:900]))
