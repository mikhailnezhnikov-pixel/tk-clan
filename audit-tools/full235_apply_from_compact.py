#!/usr/bin/env python3
import lzma, hashlib
from pathlib import Path
raw=lzma.decompress(Path("/tmp/full235-attrs2.bin.xz").read_bytes())
assert len(raw)==306001
assert hashlib.sha256(raw).hexdigest()=="728d33fbc57105109cd67f3b46de61d27bc2c4c597b9b88012952c0ad3cf0dbf"
start=815+152593
print("FULL235_ATTRS2_PROBE_ONLY=PASS")
print("ATTRS2_GEN_OFFSET=",start)
print("ATTRS2_GEN_WINDOW_HEX=",raw[start:start+160].hex())
print("ATTRS2_GEN_WINDOW_LIST=",list(raw[start:start+80]))
