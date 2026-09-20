from pathlib import Path
import re,base64,gzip

p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
MARKER="const HK_PITS_CANON_CORE_REV = 'pits-kokkaras-core-20260920-r1';"
if MARKER in s: raise SystemExit('already applied')
if "// @version      1.17.4" not in s: raise SystemExit('version mismatch')
if "HK_TODAY_TOOLBAR_REV = 'today-toolbar-clean-20260920-r3'" not in s: raise SystemExit('Today r3 base missing')
CORE_GZ="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"
core=gzip.decompress(base64.b64decode(CORE_GZ)).decode('utf-8')
anchor="  const HK_TODAY_TOOLBAR_REV = 'today-toolbar-clean-20260920-r3';\n"
s=s.replace(anchor,anchor+'  '+MARKER+'\n',1)
anchor2="  async function pitLoop() {\n"
if anchor2 not in s: raise SystemExit('pitLoop anchor missing')
s=s.replace(anchor2,core+anchor2,1)
pattern=r'''      <div class="hk-page" data-content="pit">\s*<div class="hk-cardbox">.*?</div>\s*</div>\s*      <div class="hk-page" data-content="routines">'''
replacement='''      <div class="hk-page" data-content="pit">
        <div class="hk-cardbox"><h3>${either('Ямы','Pits')}</h3><div id="hk-pits-canon"><p class="hk-muted">${either('Считываю live-состояние трёх Ям…','Reading live state of all three Pits…')}</p></div><button id="hk-pits-canon-start" class="hk-primary">${either('Запустить выбранные Ямы','Run selected Pits')}</button></div>
      </div>
      <div class="hk-page" data-content="routines">'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'pit page replacement count={n}')
pattern=r'''    root\.querySelector\('#hk-pit-start'\)\.onclick = async \(\) => \{.*?    root\.querySelector\('#hk-export'\)\.onclick = exportPowers;\n'''
replacement="    root.querySelector('#hk-pits-canon-start').onclick = pitCanonRun;\n"
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'pit handler replacement count={n}')
old="""        if (key === 'pit') {
          playerDocument = await apiJson('/player/me','POST');
          acceptPitDocument(`${apiBase}/player/me`,playerDocument);
          updatePitStatus(pitState()); updatePitButtons();
          liveReadOk=true;return playerDocument;
        }"""
new="""        if (key === 'pit') {
          const value=await pitCanonReadLive();
          liveReadOk=true;return value;
        }"""
if old not in s: raise SystemExit('refresh pit branch missing')
s=s.replace(old,new,1)
for needle in [MARKER,'const PIT_CANON_DEFINITIONS = [','function pitCanonRender()','async function pitCanonReadLive()','async function pitCanonFinishActive','async function pitCanonRun()','id="hk-pits-canon"','id="hk-pits-canon-start"',"root.querySelector('#hk-pits-canon-start').onclick = pitCanonRun"]:
    if needle not in s: raise SystemExit('missing invariant: '+needle)
for forbidden in ['id="hk-pit-start"','id="hk-pit-stop"','id="hk-target"','id="hk-activation-limit"','id="hk-restore-limit"','id="hk-pit-collect-only"','await pitLoop();']:
    if forbidden in s: raise SystemExit('legacy residue: '+forbidden)
p.write_text(s,encoding='utf-8')
print('PITS_CANON_CORE_R1_PATCH_OK')
