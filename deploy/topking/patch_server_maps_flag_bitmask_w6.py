from pathlib import Path
TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")
old='''        if not 0 <= rooms <= 5:
            continue
        investment = old_flag >= 7
        points[slot] = rooms + 8 if investment else rooms
'''
new='''        if not 0 <= rooms <= 7:
            continue
        investment_bit = old_flag & 0x08
        points[slot] = investment_bit | rooms
'''
if old not in s:
    raise SystemExit("W4 flag overlay anchor missing")
s=s.replace(old,new,1)
if "investment_bit = old_flag & 0x08" not in s:
    raise SystemExit("bitmask patch missing")
TARGET.write_text(s,encoding="utf-8")
