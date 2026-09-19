from pathlib import Path

TARGET = Path("/tmp/HamsterKingMobile.user.js")
PIT_REV = "pit-live-verify-20260920-r1"
PIT_MARKER = f"// HK_PIT_LIVE_VERIFY_V1 {PIT_REV}"
MUT_REV = "mutation-retry-live-20260920-r1"
MUT_MARKER = f"// HK_MUTATION_RETRY_LIVE_V1 {MUT_REV}"

def require(text, needle, message):
    if needle not in text:
        raise SystemExit(message)

def replace_once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"Pit live verification anchor missing: {label}")

def read_only_block(text):
    start = text.find("  const HK_READ_ONLY_POST_PATHS = new Set([")
    end = text.find("\n  ]);", start)
    if start < 0 or end < 0:
        raise SystemExit("Mutation read-only path block missing")
    return start, end + len("\n  ]);")

def apply_pit_live_hotfix(text):
    require(text, "// @version      1.17.0", "Pit verification requires live 1.17.0")
    require(text, "HK_MUTATION_GATE_REV = 'stage1-20260919-r4'", "Stage 1 mutation gate missing")
    require(text, "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'", "Hamsters must use Caps")
    require(text, "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'", "Generals must use Pit Tokens")
    require(text, "hkRunner.stop('pit')", "Pit Stop is missing")
    require(text, "title:either('Яма','Pit')", "Pit Runner start is missing")

    # Stop/Pause must be able to interrupt the short window between opening
    # a token payment dialog and confirming the irreversible spend.
    text = replace_once(
        text,
        "        await sleep(400);\n        acted = await clickEntranceToken();",
        "        await gameRetryDelay(400);\n"
        "        if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "        acted = await clickEntranceToken();",
        "Pit entry token pre-confirm delay",
    )
    text = replace_once(
        text,
        "        target.click(); await sleep(450);\n"
        "        const next = confirm(); if (next) next.click();",
        "        target.click(); await gameRetryDelay(450);\n"
        "        if (hkRunner.running) await hkRunner.waitIfPaused();\n"
        "        const next = confirm(); if (next) next.click();",
        "Pit entry token confirmation delay",
    )

    # /player/event performs resource exchanges. It must never bypass the
    # mutation FIFO merely because it uses POST as a read path elsewhere.
    ro_start, ro_end = read_only_block(text)
    ro = text[ro_start:ro_end]
    ro = ro.replace("    '/player/event',\n", "").replace("    '/player/event'\n", "")
    text = text[:ro_start] + ro + text[ro_end:]

    # A network timeout after an irreversible POST is ambiguous: the server
    # may already have applied it. Never auto-repeat mutations.
    old_route = "() => apiJsonCore(path, method, body, retryAuthorization, retryNetwork)"
    safe_route = "() => apiJsonCore(path, method, body, retryAuthorization, 0)"
    if old_route in text:
        text = text.replace(old_route, safe_route, 1)
    elif safe_route not in text:
        positions = []
        needle = "apiJsonCore(path, method, body, retryAuthorization"
        pos = 0
        while True:
            pos = text.find(needle, pos)
            if pos < 0:
                break
            positions.append(text[max(0,pos-160):min(len(text),pos+260)])
            pos += len(needle)
        raise SystemExit("Mutation routing anchor unknown: " + " | ".join(positions[:4]))

    # Keep visible revisions close to the architecture revisions so a later
    # read-only capture can prove which hardening is installed.
    arch = "  const HK_STAGE2_RUNNER_REV = 'stage2a-20260919-r1';"
    require(text, arch, "Stage 2A Pit runner revision missing")
    marker_lines = []
    if PIT_MARKER not in text:
        marker_lines.append(f"  {PIT_MARKER}")
    if MUT_MARKER not in text:
        marker_lines.append(f"  {MUT_MARKER}")
    if marker_lines:
        text = text.replace(arch, arch + "\n" + "\n".join(marker_lines), 1)

    # Final fail-closed verification.
    ro_start, ro_end = read_only_block(text)
    ro = text[ro_start:ro_end]
    if "'/player/event'" in ro:
        raise SystemExit("/player/event is still classified read-only")
    checks = [
        PIT_MARKER,
        MUT_MARKER,
        "await gameRetryDelay(400);",
        "target.click(); await gameRetryDelay(450);",
        "if (hkRunner.running) await hkRunner.waitIfPaused();",
        safe_route,
        "hkRunner.stop('pit')",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(text, needle, f"Pit verification check failed: {needle}")
    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    patched = apply_pit_live_hotfix(source)
    TARGET.write_text(patched, encoding="utf-8")
    print("PIT_LIVE_1170_VERIFY_OK")
