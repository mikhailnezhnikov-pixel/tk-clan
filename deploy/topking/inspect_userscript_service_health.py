from __future__ import annotations
import re, subprocess, urllib.request, urllib.error
from pathlib import Path

SERVICE="hamsterking-license.service"
PUBLIC="https://hk-license.89.125.1.71.sslip.io/panel.js"

def run(args, timeout=8):
    try:
        p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        return p.returncode,p.stdout.strip()
    except Exception as exc:
        return 99,f"{type(exc).__name__}: {exc}"

def fetch(url, timeout=5):
    req=urllib.request.Request(url,headers={"User-Agent":"hk-health-inspect/1"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read(240)
            return r.status,dict(r.headers),body
    except urllib.error.HTTPError as exc:
        body=exc.read(240)
        return exc.code,dict(exc.headers),body
    except Exception as exc:
        return 0,{},f"{type(exc).__name__}: {exc}".encode()

_, active=run(["systemctl","is-active",SERVICE])
_, pid_text=run(["systemctl","show",SERVICE,"-p","MainPID","--value"])
_, sub=run(["systemctl","show",SERVICE,"-p","SubState","--value"])
_, result=run(["systemctl","show",SERVICE,"-p","Result","--value"])
pid=int(pid_text or "0") if (pid_text or "").isdigit() else 0

print("USERSCRIPT_SERVICE_HEALTH_INSPECT=1")
print("ACTIVE",active)
print("SUBSTATE",sub)
print("RESULT",result)
print("MAIN_PID",pid)

rc, ss=run(["ss","-ltnp"])
ports=[]
if rc==0 and pid>0:
    for line in ss.splitlines():
        if f"pid={pid}," not in line:
            continue
        m=re.search(r"\s(?:\[[^\]]+\]|[^\s]+):(\d+)\s",line)
        if m:
            ports.append(int(m.group(1)))
ports=sorted(set(ports))
print("LISTEN_PORTS",",".join(map(str,ports)) if ports else "NONE")

for port in ports:
    for path in ["/panel.js","/health","/"]:
        status,headers,body=fetch(f"http://127.0.0.1:{port}{path}")
        ctype=headers.get("Content-Type","")
        print(f"LOCAL port={port} path={path} status={status} content_type={ctype!r} bytes={len(body)}")

status,headers,body=fetch(PUBLIC,timeout=8)
print("PUBLIC status",status,"content_type",repr(headers.get("Content-Type","")),"bytes",len(body))
if status not in (200,0):
    print("PUBLIC_BODY_PREFIX",body.decode("utf-8","replace")[:180].replace("\n"," "))

# Show only recent service lines useful for readiness failures; redact long token-like chunks.
rc,journal=run(["journalctl","-u",SERVICE,"--since","-4 min","--no-pager","-n","120"],timeout=10)
if rc==0:
    keep=[]
    for line in journal.splitlines():
        if re.search(r"error|exception|traceback|listen|started|stopped|failed|bind|address|uvicorn|gunicorn|werkzeug|ready|version",line,re.I):
            line=re.sub(r"(?<![A-Za-z0-9])[A-Za-z0-9_\-]{40,}(?![A-Za-z0-9])","[REDACTED]",line)
            keep.append(line)
    print("JOURNAL_FILTERED_BEGIN")
    print("\n".join(keep[-60:]) if keep else "(no matching lines)")
    print("JOURNAL_FILTERED_END")


print("FILESYSTEM_DIAGNOSTICS_BEGIN")
for args,label in [
    (["findmnt","-no","SOURCE,FSTYPE,OPTIONS","/"],"ROOT_MOUNT"),
    (["findmnt","-no","SOURCE,FSTYPE,OPTIONS","/opt"],"OPT_MOUNT"),
    (["findmnt","-no","SOURCE,FSTYPE,OPTIONS","/var"],"VAR_MOUNT"),
    (["df","-hT","/","/opt","/var","/tmp"],"DF"),
    (["df","-i","/","/opt","/var","/tmp"],"DF_INODES"),
    (["lsblk","-f"],"LSBLK"),
    (["systemctl","show",SERVICE,"-p","ExecStart","--value"],"EXECSTART"),
]:
    rc,out=run(args,timeout=10)
    print(label,"rc="+str(rc))
    print(out[:5000])

for directory in ["/tmp","/opt/hamsterking-license","/var/tmp"]:
    probe=Path(directory)/".hk_write_probe"
    try:
        probe.write_text("probe",encoding="utf-8")
        probe.unlink(missing_ok=True)
        print("WRITE_PROBE",directory,"OK")
    except Exception as exc:
        print("WRITE_PROBE",directory,"FAIL",type(exc).__name__,str(exc)[:200])

rc,out=run(["find","/opt/hamsterking-license","-maxdepth","3","-type","f","(","-name","*.db","-o","-name","*.sqlite","-o","-name","*.sqlite3",")","-printf","%p %s bytes %m mode\\n"],timeout=10)
print("SQLITE_FILES rc="+str(rc))
print(out[:5000] if out else "(none found)")

rc,klog=run(["journalctl","-k","--since","-20 min","--no-pager","-n","300"],timeout=12)
print("KERNEL_STORAGE_FILTER_BEGIN")
if rc==0:
    rows=[line for line in klog.splitlines() if re.search(r"I/O error|read-only|readonly|EXT4|XFS|BTRFS|buffer|filesystem|nvme|vda|sda",line,re.I)]
    print("\n".join(rows[-100:]) if rows else "(no matching kernel lines)")
else:
    print(klog[:2000])
print("KERNEL_STORAGE_FILTER_END")
print("FILESYSTEM_DIAGNOSTICS_END")
