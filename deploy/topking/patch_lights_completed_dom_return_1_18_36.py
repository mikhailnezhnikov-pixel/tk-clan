from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.35",
    "// @version      1.18.36\n// @release-note Лампочки/Автокарта: завершение комнаты теперь определяется не только временным JS-флагом, но и реальным состоянием центральной награды «Активировано», поэтому возврат работает после перерисовки/перезапуска раннера. Зависший раннер Автоламп после забора награды принудительно отпускается. Для выхода приоритет отдан нижней золотой кнопке возврата в игровом футере; правый плавающий Back/HK-контрол исключён.",
    "version")
rep("const BUILD_VERSION = '1.18.35';",
    "const BUILD_VERSION = '1.18.36';",
    "build")
rep("  const HK_LIGHTS_MAP_RETURN_REV = 'lights-map-return-after-main-reward-20260927-r1';",
    "  const HK_LIGHTS_MAP_RETURN_REV = 'lights-map-return-after-main-reward-20260927-r1';\n  const HK_LIGHTS_COMPLETED_RETURN_REV = 'lights-completed-dom-return-20260927-r2';",
    "revision")

old_reward="""    function lightsRewardElement() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_lights_out_reward_slot"]')]
        .find(element=>visible(element)) || null;
    }

"""
new_reward="""    function lightsRewardElement() {
      return [...document.querySelectorAll('[data-lot-id*="mf_fairlot_lights_out_reward_slot"]')]
        .find(element=>visible(element)) || null;
    }

    function lightsRewardActivated() {
      const reward=lightsRewardElement();
      if (!reward) return false;
      const text=clean(reward.innerText||reward.textContent||'').trim();
      const aria=clean(
        reward.getAttribute?.('aria-label') ||
        reward.getAttribute?.('title') ||
        ''
      ).trim();
      const cls=String(reward.className||'');
      return /(?:^|\\s)(?:Активировано|Activated)(?:\\s|$)/i.test(text+' '+aria)
        || /activated|claimed|completed|bought/i.test(cls);
    }

    function lightsRoomCompleted() {
      return !!(lightsFinalRewardClaimed || lightsRewardActivated());
    }

"""
rep(old_reward,new_reward,"completed reward DOM detection")

rep("""    function lightsShouldAuto() {
      if (lightsFinalRewardClaimed) return false;
      return lightsNeedsAuto() || !!lightsRewardElement();
    }
""",
"""    function lightsShouldAuto() {
      if (lightsRoomCompleted()) return false;
      return lightsNeedsAuto() || !!lightsRewardElement();
    }
""",
"lightsShouldAuto completed DOM")

# Replace old back finder with footer-first version.
start=s.find("    function autoMapCompletedLightsBackButton() {")
end=s.find("\n    async function autoMapWaitReturnedFromLights",start)
if start<0 or end<0:
    raise SystemExit("autoMapCompletedLightsBackButton block not found")
new_back="""    function autoMapCompletedLightsBackButton() {
      if (!lightsRoomCompleted()) return null;

      const viewportW=Math.max(1,window.innerWidth);
      const viewportH=Math.max(1,window.innerHeight);
      const all=[...document.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>
          element &&
          element!==autoMapToggle &&
          element!==battleAutoToggle &&
          element!==chestAutoToggle &&
          element!==lightsAutoToggle &&
          element!==fishingAutoToggle &&
          element!==traderAutoToggle &&
          !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const aria=clean(
            element.getAttribute?.('aria-label') ||
            element.getAttribute?.('title') ||
            element.getAttribute?.('data-tooltip') ||
            ''
          ).trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a,[onclick]') ||
            !!element.onclick ||
            style.cursor==='pointer';
          const hasIcon=!!element.querySelector?.('svg,img,use,path') || /[←↩⟵‹«]/.test(text);
          const explicitBack=/назад|back|return|вернуться|покинуть|leave|exit/i.test(text+' '+aria);
          return {element,text,aria,rect,actionable,hasIcon,explicitBack};
        })
        .filter(row=>row.actionable && row.rect.width>0 && row.rect.height>0);

      // Canonical desktop/mobile layout: the real room-return control is the
      // small gold square in the bottom game footer, immediately left of the
      // wide yellow cost/continue bar. Prefer that region over any floating HK
      // or browser-like back controls on the right edge.
      const footer=all
        .map(row=>{
          const r=row.rect;
          const cx=r.left+r.width/2;
          const cy=r.top+r.height/2;
          const squareish=
            r.width>=26 && r.width<=100 &&
            r.height>=26 && r.height<=100 &&
            r.width/Math.max(1,r.height)>=0.55 &&
            r.width/Math.max(1,r.height)<=1.85;
          const footerY=cy>=viewportH*0.86;
          const gameBand=cx>=viewportW*0.20 && cx<=viewportW*0.55;
          const farRight=cx>=viewportW*0.82;
          let score=0;
          if (squareish) score+=180;
          if (footerY) score+=260;
          if (gameBand) score+=240;
          if (row.hasIcon) score+=100;
          if (row.explicitBack) score+=120;
          if (!row.text || /^[←↩⟵‹«]$/.test(row.text)) score+=55;
          if (farRight) score-=800;
          if (r.width>130 || r.height>120) score-=700;
          if (/^\\d+$/.test(row.text)) score-=700;
          if (/^hk$/i.test(row.text)) score-=900;
          if (/автокарта|автолампы|auto\\s*map|auto\\s*lights/i.test(row.text)) score-=900;
          return {...row,score};
        })
        .filter(row=>row.score>=500)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);

      if (footer[0]?.element) return footer[0].element;

      // Secondary fallback: explicit textual/icon back controls, but never the
      // right floating control visible in the HK overlay.
      const fallback=all
        .map(row=>{
          const r=row.rect;
          const cx=r.left+r.width/2;
          const cy=r.top+r.height/2;
          const farRight=cx>=viewportW*0.82;
          let score=0;
          if (row.explicitBack) score+=360;
          if (row.hasIcon) score+=90;
          if (cy>=viewportH*0.60) score+=70;
          if (cx<=viewportW*0.70) score+=90;
          if (farRight) score-=800;
          if (r.width>130 || r.height>120) score-=500;
          if (/^hk$/i.test(row.text)) score-=900;
          return {...row,score};
        })
        .filter(row=>row.score>=300)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);

      return fallback[0]?.element || null;
    }
"""
s=s[:start]+new_back+s[end:]

# Allow completed DOM state even if transient in-memory flag was lost.
rep("""    async function autoMapReturnFromCompletedLights() {
      if (!autoMapEnabled() || !lightsFinalRewardClaimed) return false;

      autoMapStatus('возврат на карту',{
        revision:HK_LIGHTS_MAP_RETURN_REV,
        claimedAgoMs:lightsFinalRewardClaimedAt ? Date.now()-lightsFinalRewardClaimedAt : null
      });

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !lightsFinalRewardClaimed) return false;
""",
"""    async function autoMapReturnFromCompletedLights() {
      if (!autoMapEnabled() || !lightsRoomCompleted()) return false;

      if (!lightsFinalRewardClaimed && lightsRewardActivated()) {
        lightsFinalRewardClaimed=true;
        lightsFinalRewardClaimedAt=Date.now();
        recordDiagnostic('lights-final-reward-recovered',{
          revision:HK_LIGHTS_COMPLETED_RETURN_REV,
          source:'activated-reward-dom'
        });
      }

      autoMapStatus('возврат на карту',{
        revision:HK_LIGHTS_COMPLETED_RETURN_REV,
        claimedAgoMs:lightsFinalRewardClaimedAt ? Date.now()-lightsFinalRewardClaimedAt : null
      });

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !lightsRoomCompleted()) return false;
""",
"completed DOM return entry")

# Replace in-function strict checks that require only in-memory flag.
s=s.replace("if (autoMapEnabled() && lightsFinalRewardClaimed) {",
            "if (autoMapEnabled() && lightsRoomCompleted()) {",1)

# Recover/cancel stale lights runner before generic module-running gate.
old_gate="""      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }

      if (autoMapModulesRunning()) {
"""
new_gate="""      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }

      // After the central reward is visibly Activated, the lights runner has no
      // more work. Release a stale runner before the generic "mini-game busy"
      // gate, otherwise AutoMap can remain forever on "мини-игра".
      if (lightsRoomCompleted() && getSignature().startsWith('LIGHTS|') && lightsAutoRunning) {
        lightsAutoRunId+=1;
        lightsAutoRunning=false;
        lastSignature='';
        recordDiagnostic('lights-completed-runner-release',{
          revision:HK_LIGHTS_COMPLETED_RETURN_REV,
          activated:lightsRewardActivated()
        });
      }

      if (autoMapModulesRunning()) {
"""
rep(old_gate,new_gate,"release stale completed lights runner")

# Strict branch should use real completed state, not only volatile flag.
rep("""        if (lightsFinalRewardClaimed && getSignature().startsWith('LIGHTS|')) {
          return await autoMapReturnFromCompletedLights();
        }
""",
"""        if (lightsRoomCompleted() && getSignature().startsWith('LIGHTS|')) {
          return await autoMapReturnFromCompletedLights();
        }
""",
"strict completed lights return")

# Do not erase the recovered flag while still in the activated lights room.
rep("""      if (!isLights && lightsFinalRewardClaimed) {
        lightsFinalRewardClaimed=false;
        lightsFinalRewardClaimedAt=0;
        recordDiagnostic('lights-final-reward-reset',{
          revision:HK_LIGHTS_MAP_RETURN_REV,
          reason:'left-lights-screen'
        });
      }
""",
"""      if (!isLights && lightsFinalRewardClaimed) {
        lightsFinalRewardClaimed=false;
        lightsFinalRewardClaimedAt=0;
        recordDiagnostic('lights-final-reward-reset',{
          revision:HK_LIGHTS_COMPLETED_RETURN_REV,
          reason:'left-lights-screen'
        });
      } else if (isLights && !lightsFinalRewardClaimed && lightsRewardActivated()) {
        lightsFinalRewardClaimed=true;
        lightsFinalRewardClaimedAt=Date.now();
        recordDiagnostic('lights-final-reward-recovered',{
          revision:HK_LIGHTS_COMPLETED_RETURN_REV,
          source:'check-puzzle-activated-dom'
        });
      }
""",
"recover completed flag in checkPuzzle")

rep("      lightsMapReturnRevision:HK_LIGHTS_MAP_RETURN_REV,\n      start,",
    "      lightsMapReturnRevision:HK_LIGHTS_MAP_RETURN_REV,\n      lightsCompletedReturnRevision:HK_LIGHTS_COMPLETED_RETURN_REV,\n      start,",
    "export completed return revision")

for marker in [
    "// @version      1.18.36",
    "const BUILD_VERSION = '1.18.36';",
    "lights-completed-dom-return-20260927-r2",
    "function lightsRewardActivated()",
    "function lightsRoomCompleted()",
    "lights-completed-runner-release",
    "check-puzzle-activated-dom",
    "const footer=all",
    "cx>=viewportW*0.20 && cx<=viewportW*0.55",
    "farRight",
    "lights-map-return-complete",
    "lights-reward-bottom-action-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_COMPLETED_DOM_RETURN_1_18_36=PASS")
