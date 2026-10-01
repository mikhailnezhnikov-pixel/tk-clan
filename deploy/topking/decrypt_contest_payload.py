"""Decrypt on the target server only; no content or credentials printed."""
import base64,hashlib,hmac,json,subprocess,tempfile,shutil
from pathlib import Path
import sys
payload=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp);(t/'wrapped').write_bytes(base64.b64decode(payload['key']))
    shutil.copyfile('/etc/ssh/ssh_host_rsa_key',t/'host-key');(t/'host-key').chmod(0o600)
    subprocess.run(['ssh-keygen','-p','-m','PEM','-P','','-N','','-f',str(t/'host-key')],check=True,capture_output=True)
    subprocess.run(['openssl','pkeyutl','-decrypt','-inkey',str(t/'host-key'),'-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-in',str(t/'wrapped'),'-out',str(t/'key')],check=True,capture_output=True)
    key=(t/'key').read_bytes();cipher=base64.b64decode(payload['cipher'])
    assert hmac.compare_digest(hmac.new(key,cipher,hashlib.sha256).hexdigest(),payload['mac']),'Encrypted payload authentication failed'
    (t/'cipher').write_bytes(cipher)
    subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000','-in',str(t/'cipher'),'-out',str(t/'plain'),'-pass','file:'+str(t/'key')],check=True,capture_output=True)
    for name,value in json.loads((t/'plain').read_text()).items():
        assert name in ('contest_content.json','contest_material.json')
        target=Path(sys.argv[2])/name;target.write_text(json.dumps(value,ensure_ascii=False));target.chmod(0o600)
print('PRIVATE_CONTENT_DECRYPTED=PASS')
