from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_TEST_HISTORY_RESET_V1"

s, n1 = re.subn(
    r'\n# CLAN_SHOP_TEST_HISTORY_RESET_V1\ndef reset_clan_shop_test_history\(member: dict\) -> dict:\n.*?\n\ndef clan_shop_history_payload\(\) -> dict:\n',
    '\n\ndef clan_shop_history_payload() -> dict:\n',
    s,
    count=1,
    flags=re.S,
)

s, n2 = re.subn(
    r'''            elif path == "/api/v1/cabinet/clan-shop/reset-test-history":\n.*?            elif path in \("/api/v1/cabinet/clan-shop/set",\n''',
    '''            elif path in ("/api/v1/cabinet/clan-shop/set",\n''',
    s,
    count=1,
    flags=re.S,
)

if MARKER in s or "/api/v1/cabinet/clan-shop/reset-test-history" in s:
    raise SystemExit("reset endpoint cleanup incomplete")

path.write_text(s)
print("CLAN_SHOP_TEST_HISTORY_RESET_REMOVED", n1, n2)
