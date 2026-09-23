from pathlib import Path

path=Path('/tmp/HamsterKingMobile.user.js')
s=path.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global s
    count=s.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    s=s.replace(old,new,1)

for required in [
    "// @version      1.17.82",
    "const BUILD_VERSION = '1.17.82';",
    "runtime-smoke-capture-20260924-r1",
    "userscript-update-metadata-20260924-r1",
]:
    if required not in s:
        raise SystemExit('missing source marker: '+required)

replace_once(
    "// @version      1.17.82\n",
    "// @version      1.17.83\n"
    "// @release-note Диагностика: общий индикатор «Сервер» теперь отражает контрольную проверку основного HK-сервера; сбой отдельного фонового endpoint остаётся в диагностике и больше не создаёт ложный красный статус.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.82';",
    "const BUILD_VERSION = '1.17.83';",
    'build version'
)

replace_once(
    "  const SERVER_REQUEST_RETRY_DELAYS_MS = [1000, 3000, 7000];\n",
    "  const SERVER_REQUEST_RETRY_DELAYS_MS = [1000, 3000, 7000];\n"
    "  const HK_SERVER_HEALTH_SCOPE_REV = 'server-health-core-20260924-r1';\n",
    'server health marker'
)

replace_once(
    "        setHealth('server', false, error?.name==='HKNetworkTimeout'?'тайм-аут':'ошибка сети');\n"
    "        throw error;\n",
    "        recordDiagnostic('server-endpoint-unavailable',{revision:HK_SERVER_HEALTH_SCOPE_REV,label,path,kind:error?.name==='HKNetworkTimeout'?'timeout':'network'});\n"
    "        throw error;\n",
    'optional network failure health'
)

replace_once(
    "      if (!response.ok || !value) {\n"
    "        setHealth('server', false, `HTTP ${response.status}`);\n"
    "        throw new Error(`HTTP ${response.status}: ${text.slice(0, 120)}`);\n"
    "      }\n"
    "      setHealth('server', true, 'сервер отвечает');\n"
    "      return value;\n",
    "      if (!response.ok || !value) {\n"
    "        recordDiagnostic('server-endpoint-unavailable',{revision:HK_SERVER_HEALTH_SCOPE_REV,label,path,kind:'http',status:response.status});\n"
    "        throw new Error(`HTTP ${response.status}: ${text.slice(0, 120)}`);\n"
    "      }\n"
    "      return value;\n",
    'optional http health'
)

for marker in [
    "// @version      1.17.83",
    "const BUILD_VERSION = '1.17.83';",
    "server-health-core-20260924-r1",
    "runtime-smoke-capture-20260924-r1",
    "userscript-update-metadata-20260924-r1",
    "server-endpoint-unavailable",
]:
    if marker not in s:
        raise SystemExit('missing target marker: '+marker)

# Only the authoritative license/core check may mutate the global server health chip.
if s.count("setHealth('server'") != 2:
    raise SystemExit("unexpected global server health writers: "+str(s.count("setHealth('server'")))
if "setHealth('server', response.ok" not in s:
    raise SystemExit('authoritative server health success/failure writer missing')
if "setHealth('server', false, 'сервер недоступен')" not in s:
    raise SystemExit('authoritative server network failure writer missing')

path.write_text(s,encoding='utf-8')
print('PATCH_1_17_83_SERVER_HEALTH_SCOPE=PASS')
