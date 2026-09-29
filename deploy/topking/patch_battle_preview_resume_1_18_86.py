from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.85",
    "// @version      1.18.86\n// @release-note Карта сокровищ — Сражение: исправлен зависший предпросмотр. Фоновая модалка Золотых монет больше не перехватывает Автокарту; если окно Сражения уже открыто, Автокарта сама нажимает кнопку входа с ягодами и продолжает бой.",
    "version")
rep("const BUILD_VERSION = '1.18.85';",
    "const BUILD_VERSION = '1.18.86';",
    "build")
rep("  const HK_BATTLE_INTRO_HARD_GATE_REV='battle-intro-hard-gate-20260929-r1';",
    "  const HK_BATTLE_INTRO_HARD_GATE_REV='battle-intro-hard-gate-20260929-r1';\n  const HK_BATTLE_PREVIEW_RESUME_REV='battle-preview-resume-20260929-r1';",
    "revision")

old_gold="""        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.35) && row.rect.height>=180)
        .filter(row=>row.exactTitle && row.purchaseText)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
"""
new_gold="""        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.35) && row.rect.height>=180)
        .filter(row=>row.exactTitle && row.purchaseText)
        // A stale trader modal can remain mounted behind the current Treasure Map
        // preview. Geometry alone is not enough: only the frontmost modal may own
        // AutoMap. This prevents a hidden Gold Coins window from blocking Battle.
        .filter(row=>{
          const r=row.rect;
          const points=[
            [r.left+r.width*0.50,r.top+r.height*0.50],
            [r.left+r.width*0.35,r.top+r.height*0.68],
            [r.left+r.width*0.65,r.top+r.height*0.68]
          ];
          return points.some(([x,y])=>{
            const px=Math.max(1,Math.min(window.innerWidth-1,x));
            const py=Math.max(1,Math.min(window.innerHeight-1,y));
            const top=document.elementFromPoint(px,py);
            return !!top && (top===row.element || row.element.contains(top));
          });
        })
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
"""
rep(old_gold,new_gold,"foreground gold guard")

anchor="    function autoMapTreasureKeyModalRoot() {"
helper=r'''    function autoMapBattlePreviewRoot() {
      if (!treasureGuideScreenVisible()) return null;
      const battleTitle=/(?:^|
)s*(?:Сражение|Battle)s*(?:
|$)/i;
      const previewCopy=/(?:Можноs+отыскать|Cans+bes+found|Yous+cans+find)/i;
      const rows=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const action=autoMapModalPrimaryButton(element,null);
          const points=[
            [rect.left+rect.width*0.50,rect.top+rect.height*0.50],
            [rect.left+rect.width*0.50,rect.top+rect.height*0.78]
          ];
          const foreground=points.some(([x,y])=>{
            const px=Math.max(1,Math.min(window.innerWidth-1,x));
            const py=Math.max(1,Math.min(window.innerHeight-1,y));
            const top=document.elementFromPoint(px,py);
            return !!top && (top===element || element.contains(top));
          });
          return {element,text,rect,action,foreground,area:rect.width*rect.height};
        })
        .filter(row=>row.foreground)
        .filter(row=>row.rect.width>=Math.min(280,window.innerWidth*0.38) && row.rect.height>=220)
        .filter(row=>battleTitle.test(row.text) && previewCopy.test(row.text))
        .filter(row=>row.action)
        .filter(row=>!/Сундук победителя|Victory chest|Winner chest|Понятно|Got it|Understood/i.test(row.text))
        .sort((a,b)=>a.area-b.area);
      return rows[0]?.element || null;
    }

    async function autoMapResumeBattlePreview(root=autoMapBattlePreviewRoot()) {
      if (!autoMapEnabled() || !root) return false;
      const action=autoMapModalPrimaryButton(root,null);
      if (!action) {
        autoMapStatus('сражение → жду кнопку входа',{
          revision:HK_BATTLE_PREVIEW_RESUME_REV
        });
        return false;
      }

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !root.isConnected) return false;

      const before=autoMapStateFingerprint();
      const runId=autoMapRunId;
      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();
      autoMapStatus('сражение → запускаю',{
        revision:HK_BATTLE_PREVIEW_RESUME_REV,
        text:clean(action.innerText||action.textContent||'').trim().slice(0,40)
      });

      if (!dispatchAutoMapTap(action,'battle-preview-start')) {
        autoMapRetryNotBefore=Date.now()+500;
        return false;
      }

      const started=Date.now();
      while (Date.now()-started<4500) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;
        const intro=battleIntroModalRoot();
        const sig=getSignature();
        if (intro || sig.startsWith('BATTLE') || !autoMapBattlePreviewRoot() || autoMapStateFingerprint()!==before) {
          autoMapRetryNotBefore=0;
          autoMapCurrentLot='';
          lastSignature='';
          recordDiagnostic('battle-preview-resumed',{
            revision:HK_BATTLE_PREVIEW_RESUME_REV,
            intro:!!intro,
            signature:sig.slice(0,120)
          });
          setTimeout(()=>{
            checkPuzzle();
            void runAutoMapTick('battle-preview-resumed');
          },120);
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      autoMapRetryNotBefore=Date.now()+650;
      autoMapStatus('сражение → жду вход',{
        revision:HK_BATTLE_PREVIEW_RESUME_REV
      });
      setTimeout(()=>void runAutoMapTick('battle-preview-retry'),760);
      return false;
    }

'''
if s.count(anchor)!=1:
    raise SystemExit("battle preview helper anchor missing")
s=s.replace(anchor,helper+anchor,1)

preflight="""      const introHardGate=battleIntroModalRoot();
"""
insert=r'''      const openBattlePreview=autoMapBattlePreviewRoot();
      if (openBattlePreview) {
        autoMapRunning=true;
        const previewRunId=autoMapRunId;
        try {
          return await autoMapResumeBattlePreview(openBattlePreview);
        } finally {
          if (previewRunId===autoMapRunId) autoMapRunning=false;
        }
      }

'''
if s.count(preflight)!=1:
    raise SystemExit("battle preview preflight anchor missing")
s=s.replace(preflight,insert+preflight,1)

rep("      battleIntroHardGateRevision:HK_BATTLE_INTRO_HARD_GATE_REV,",
    "      battleIntroHardGateRevision:HK_BATTLE_INTRO_HARD_GATE_REV,\n      battlePreviewResumeRevision:HK_BATTLE_PREVIEW_RESUME_REV,",
    "diagnostic export")

for marker in [
    "// @version      1.18.86",
    "battle-preview-resume-20260929-r1",
    "function autoMapBattlePreviewRoot()",
    "function autoMapResumeBattlePreview(",
    "battle-preview-start",
    "document.elementFromPoint",
    "battle-intro-hard-gate-20260929-r1",
    "trader-gold-exact-purchase-modal-20260929-r1",
    "battle-visible-point-truth-20260929-r1",
    "battle-full-fair-state-20260928-r1",
    "battle-egg-one-berry-buy-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("BATTLE_PREVIEW_RESUME_1_18_86=PASS")
