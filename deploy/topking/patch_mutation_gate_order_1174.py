from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'mutation-gate-order-20260920-r1'
MARKER = f"HK_MUTATION_GATE_ORDER_REV = '{REV}'"

def require(s, needle, label):
    if needle not in s:
        raise SystemExit(f'mutation gate order check failed: {label}')

def apply(s):
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_STARTUP_ERROR_TRAP_REV = 'startup-error-trap-20260920-r8'", 'startup error trap r8')
    require(s, 'runtime.mutationGate = hkMutationGate;', 'early runtime mutation gate registration')
    require(s, 'const hkMutationGate = (() => {', 'mutation gate declaration')
    require(s, 'async function apiJson(path, method = \'GET\'', 'apiJson anchor')

    if MARKER in s:
        return validate(s)

    # Remove the top-level TDZ access that executes before hkMutationGate exists.
    s = s.replace('  runtime.mutationGate = hkMutationGate;\n', '', 1)

    # Register the gate only after the const IIFE has fully initialized.
    anchor = """  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {"""
    insertion = f"""  const {MARKER};
  runtime.mutationGate = hkMutationGate;

{anchor}"""
    if anchor not in s:
        raise SystemExit('mutation gate order anchor missing: apiJson')
    s = s.replace(anchor, insertion, 1)

    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        MARKER,
        'const hkMutationGate = (() => {',
        'runtime.mutationGate = hkMutationGate;',
        "async function apiJson(path, method = 'GET'",
    ]
    for needle in checks:
        require(s, needle, needle)

    declaration = s.find('const hkMutationGate = (() => {')
    registration = s.find('runtime.mutationGate = hkMutationGate;')
    api = s.find("async function apiJson(path, method = 'GET'", declaration)

    if min(declaration, registration, api) < 0:
        raise SystemExit('mutation gate order validation failed: missing anchors')
    if not (declaration < registration < api):
        raise SystemExit(
            f'mutation gate order validation failed: declaration={declaration} '
            f'registration={registration} api={api}'
        )

    if s.count('runtime.mutationGate = hkMutationGate;') != 1:
        raise SystemExit('mutation gate order validation failed: registration count != 1')

    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply(source), encoding='utf-8')
    print('HK_MUTATION_GATE_ORDER_FIX_OK')
