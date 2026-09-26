# build-trigger: 1.18.14 treasure recorder stability r1
from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.13",
    "// @version      1.18.14\n"
    "// @release-note Карта Сокровищ: исправлена самопетля пассивного рекордера на Safari. Добавлена запись блокирующих действий: disabled/locked, модальные запреты, нехватка ресурсов, кулдауны, HTTP 4xx/5xx и «клик без изменения состояния».",
    "version"
)
rep("const BUILD_VERSION = '1.18.13';","const BUILD_VERSION = '1.18.14';","build")

rep(
    "  const HK_TREASURE_RUN_RECORDER_REV='treasure-run-recorder-20260926-r1';",
    "  const HK_TREASURE_RUN_RECORDER_REV='treasure-run-recorder-20260926-r1';\n"
    "  const HK_TREASURE_RUN_RECORDER_STABILITY_REV='treasure-run-recorder-stability-blockers-20260926-r2';",
    "stability marker"
)

rep(
    """  let treasureRunRecorderLastFingerprint='';
  let treasureRunRecorderObserver=null;
""",
    """  let treasureRunRecorderLastFingerprint='';
  let treasureRunRecorderObserver=null;
  let treasureRunRecorderLastNetworkAt=0;
  let treasureRunRecorderLastMutationAt=0;
  let treasureRunRecorderClickSerial=0;
""",
    "recorder runtime state"
)

# Add blocker inventory before snapshot.
anchor="""  function treasureRunRecorderSnapshot(reason='dom') {
"""
helpers=r'''  function treasureRunRecorderBlockingSignals() {
    const out=[];
    const seen=new Set();
    const add=(kind,node,text='',extra={})=>{
      if(!node || out.length>=40)return;
      const rect=node.getBoundingClientRect?.();
      const value=String(text||node.innerText||node.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,700);
      const lotNode=node.closest?.('[data-lot-id]');
      const key=[kind,String(lotNode?.getAttribute?.('data-lot-id')||''),value].join('|');
      if(seen.has(key))return;
      seen.add(key);
      out.push({
        kind,
        lotId:String(lotNode?.getAttribute?.('data-lot-id')||'').slice(0,220),
        text:value,
        x:rect?Math.round(rect.left+rect.width/2):null,
        y:rect?Math.round(rect.top+rect.height/2):null,
        ...extra
      });
    };

    try{
      const disabled=[...document.querySelectorAll('button:disabled,[aria-disabled="true"],[data-disabled="true"],.disabled,[class*="locked"],[class*="blocked"]')].filter(visible);
      for(const node of disabled.slice(0,24)){
        add('disabled-or-locked',node,'',{
          disabled:!!node.disabled,
          ariaDisabled:String(node.getAttribute?.('aria-disabled')||''),
          cls:String(node.className||'').slice(0,260)
        });
      }
    }catch(_){}

    try{
      const blockerRe=/(недостаточно|не хватает|заблокирован|заблокировано|закрыто|недоступно|подождите|попробуйте позже|слишком быстро|кулдаун|перезаряд|через\s+\d|not enough|insufficient|locked|unavailable|cooldown|try again|too fast|wait\s+\d)/i;
      const nodes=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="toast"],[class*="alert"],[class*="message"]')].filter(visible);
      for(const node of nodes.slice(0,30)){
        const text=String(node.innerText||node.textContent||'').replace(/\s+/g,' ').trim();
        if(blockerRe.test(text))add('blocking-message',node,text);
      }
    }catch(_){}

    return out;
  }

  function treasureRunRecorderStateFingerprint() {
    try{
      return treasureGuideHash(JSON.stringify({
        screen:treasureRunRecorderScreen(),
        headings:treasureRunRecorderHeadings(),
        modals:treasureRunRecorderModalTexts(),
        lots:treasureRunRecorderVisibleLots().map(row=>({
          lotId:row.lotId,text:row.text,cls:row.cls,x:row.x,y:row.y
        })),
        blockers:treasureRunRecorderBlockingSignals()
      }));
    }catch(_){return '';}
  }

  function treasureRunRecorderBlockingReason(targetInfo,modals=[]) {
    const text=[
      String(targetInfo?.text||''),
      ...(Array.isArray(modals)?modals:[])
    ].join(' ');
    if(targetInfo?.disabled || targetInfo?.ariaDisabled==='true')return 'target-disabled';
    if(targetInfo?.pointerEvents==='none')return 'pointer-events-none';
    if(/недостаточно|не хватает|not enough|insufficient/i.test(text))return 'insufficient-resource';
    if(/заблок|закрыт|недоступ|locked|unavailable/i.test(text))return 'locked-or-unavailable';
    if(/подожд|попробуйте позже|слишком быстро|кулдаун|перезаряд|cooldown|try again|too fast|wait/i.test(text))return 'cooldown-or-wait';
    return '';
  }

  function treasureRunRecorderRecordBlocked(reason,data={}) {
    if(!treasureRunRecorderActive())return;
    treasureRunRecorderEvent('blocked-action',{
      revision:HK_TREASURE_RUN_RECORDER_STABILITY_REV,
      reason:String(reason||'blocked'),
      ...data
    });
  }

'''
need(anchor,"snapshot anchor")
s=s.replace(anchor,helpers+anchor,1)

# Include blockers in snapshots.
rep(
    """      modals:treasureRunRecorderModalTexts(),
      lots:treasureRunRecorderVisibleLots(),
      pageText
""",
    """      modals:treasureRunRecorderModalTexts(),
      lots:treasureRunRecorderVisibleLots(),
      blockers:treasureRunRecorderBlockingSignals(),
      pageText
""",
    "snapshot blockers"
)

# Enrich clicked target with actual blocking/disabled state.
rep(
    """    const rect=actionable.getBoundingClientRect?.();
    return {
      lotId:String(lotNode?.getAttribute?.('data-lot-id')||'').slice(0,220),
      tag:String(actionable.tagName||'').toLowerCase(),
      id:String(actionable.id||'').slice(0,120),
      cls:String(actionable.className||'').slice(0,260),
      text:String(actionable.innerText||actionable.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,900),
      x:rect?Math.round(rect.left+rect.width/2):null,
      y:rect?Math.round(rect.top+rect.height/2):null,
      w:rect?Math.round(rect.width):null,
      h:rect?Math.round(rect.height):null
    };
""",
    """    const rect=actionable.getBoundingClientRect?.();
    const style=getComputedStyle(actionable);
    return {
      lotId:String(lotNode?.getAttribute?.('data-lot-id')||'').slice(0,220),
      tag:String(actionable.tagName||'').toLowerCase(),
      id:String(actionable.id||'').slice(0,120),
      cls:String(actionable.className||'').slice(0,260),
      text:String(actionable.innerText||actionable.textContent||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().slice(0,900),
      disabled:!!actionable.disabled,
      ariaDisabled:String(actionable.getAttribute?.('aria-disabled')||''),
      ariaBusy:String(actionable.getAttribute?.('aria-busy')||''),
      pointerEvents:String(style.pointerEvents||''),
      opacity:String(style.opacity||''),
      cursor:String(style.cursor||''),
      x:rect?Math.round(rect.left+rect.width/2):null,
      y:rect?Math.round(rect.top+rect.height/2):null,
      w:rect?Math.round(rect.width):null,
      h:rect?Math.round(rect.height):null
    };
""",
    "target blocking state"
)

# Click outcome detector: records disabled immediately and no-state-change after settle.
old_click="""  function treasureRunRecorderObserveClick(event) {
    if(!treasureRunRecorderActive())return;
    const element=event.target instanceof Element?event.target:null;
    if(element?.closest?.('#hkTreasureRunRecorderToggle'))return;
    treasureRunRecorderEvent('click',{
      pointerType:String(event.pointerType||''),
      clientX:Number.isFinite(event.clientX)?Math.round(event.clientX):null,
      clientY:Number.isFinite(event.clientY)?Math.round(event.clientY):null,
      target:treasureRunRecorderTargetInfo(event.target)
    });
    treasureRunRecorderScheduleSnapshot('after-click',250);
    setTimeout(()=>treasureRunRecorderScheduleSnapshot('after-click-settle',120),900);
  }
"""
new_click="""  function treasureRunRecorderObserveClick(event) {
    if(!treasureRunRecorderActive())return;
    const element=event.target instanceof Element?event.target:null;
    if(element?.closest?.('#hkTreasureRunRecorderToggle'))return;

    const targetInfo=treasureRunRecorderTargetInfo(event.target);
    const clickId=++treasureRunRecorderClickSerial;
    const clickedAt=Date.now();
    const beforeFingerprint=treasureRunRecorderStateFingerprint();
    const beforeScreen=treasureRunRecorderScreen();
    const immediateReason=treasureRunRecorderBlockingReason(targetInfo,treasureRunRecorderModalTexts());

    treasureRunRecorderEvent('click',{
      clickId,
      pointerType:String(event.pointerType||''),
      clientX:Number.isFinite(event.clientX)?Math.round(event.clientX):null,
      clientY:Number.isFinite(event.clientY)?Math.round(event.clientY):null,
      target:targetInfo
    });

    if(immediateReason){
      treasureRunRecorderRecordBlocked(immediateReason,{
        clickId,
        phase:'before-click',
        screen:beforeScreen,
        target:targetInfo
      });
    }

    treasureRunRecorderScheduleSnapshot('after-click',250);
    setTimeout(()=>{
      if(!treasureRunRecorderActive())return;
      const afterFingerprint=treasureRunRecorderStateFingerprint();
      const afterScreen=treasureRunRecorderScreen();
      const modals=treasureRunRecorderModalTexts();
      const reason=treasureRunRecorderBlockingReason(targetInfo,modals);
      const networkSeen=treasureRunRecorderLastNetworkAt>=clickedAt;
      const mutationSeen=treasureRunRecorderLastMutationAt>=clickedAt;

      if(reason && !immediateReason){
        treasureRunRecorderRecordBlocked(reason,{
          clickId,
          phase:'after-click',
          screenBefore:beforeScreen,
          screenAfter:afterScreen,
          networkSeen,
          mutationSeen,
          target:targetInfo,
          modals
        });
      }else if(beforeFingerprint && afterFingerprint===beforeFingerprint && !networkSeen){
        treasureRunRecorderRecordBlocked('no-state-change',{
          clickId,
          phase:'after-click',
          screen:afterScreen,
          mutationSeen,
          target:targetInfo,
          modals
        });
      }
      treasureRunRecorderScheduleSnapshot('after-click-settle',100);
    },1100);
  }
"""
rep(old_click,new_click,"click blocker outcomes")

# Network error is itself a blocker and updates last network timestamp.
rep(
    """    const statusNumber=Number(status||0);
    const methodValue=String(method||'GET').toUpperCase();
    const important=treasureRunRecorderNetworkImportant(path,methodValue,statusNumber);
    treasureRunRecorderEvent('network',{
""",
    """    const statusNumber=Number(status||0);
    const methodValue=String(method||'GET').toUpperCase();
    const important=treasureRunRecorderNetworkImportant(path,methodValue,statusNumber);
    treasureRunRecorderLastNetworkAt=Date.now();
    treasureRunRecorderEvent('network',{
""",
    "network timestamp"
)

rep(
    """      response:important?treasureRunRecorderPayload(responseBody,18000):null
    });
    treasureRunRecorderScheduleSnapshot('after-network',400);
""",
    """      response:important?treasureRunRecorderPayload(responseBody,18000):null
    });
    if(statusNumber>=400){
      treasureRunRecorderRecordBlocked(
        statusNumber===409?'http-409-conflict':
        statusNumber===429?'http-429-rate-limit':
        statusNumber>=500?'http-5xx-server-error':'http-error',
        {
          path,
          method:methodValue,
          status:statusNumber,
          response:treasureRunRecorderPayload(responseBody,9000)
        }
      );
    }
    treasureRunRecorderScheduleSnapshot('after-network',400);
""",
    "network blocker events"
)

# Make UI updates idempotent: crucial Safari self-loop fix.
old_update="""  function treasureRunRecorderUpdateButton() {
    if(!treasureRunRecorderButton)return;
    const active=treasureRunRecorderActive();
    const show=active || treasureGuideScreenVisible();
    treasureRunRecorderButton.style.display=show?'block':'none';
    treasureRunRecorderButton.textContent=active
      ? 'Запись карты: ВКЛ #'+String(treasureRunRecorderState?.runIndex||'')
      : 'Запись карты: ВЫКЛ';
    treasureRunRecorderButton.style.background=active?'#d13b3b':'#292929';
    treasureRunRecorderButton.style.color='#fff';
    treasureRunRecorderButton.style.borderColor=active?'#ffd5d5':'rgba(255,255,255,.8)';
  }
"""
new_update="""  function treasureRunRecorderUpdateButton() {
    if(!treasureRunRecorderButton)return;
    const active=treasureRunRecorderActive();
    const show=active || treasureGuideScreenVisible();
    const display=show?'block':'none';
    const label=active
      ? 'Запись карты: ВКЛ #'+String(treasureRunRecorderState?.runIndex||'')
      : 'Запись карты: ВЫКЛ';
    const background=active?'#d13b3b':'#292929';
    const borderColor=active?'#ffd5d5':'rgba(255,255,255,.8)';

    if(treasureRunRecorderButton.style.display!==display)treasureRunRecorderButton.style.display=display;
    if(treasureRunRecorderButton.textContent!==label)treasureRunRecorderButton.textContent=label;
    if(treasureRunRecorderButton.style.background!==background)treasureRunRecorderButton.style.background=background;
    if(treasureRunRecorderButton.style.color!=='rgb(255, 255, 255)' && treasureRunRecorderButton.style.color!=='#fff')treasureRunRecorderButton.style.color='#fff';
    if(treasureRunRecorderButton.style.borderColor!==borderColor)treasureRunRecorderButton.style.borderColor=borderColor;
  }
"""
rep(old_update,new_update,"idempotent recorder button")

# Observer ignores its own UI and no longer observes style mutations.
old_obs="""      if(!treasureRunRecorderObserver){
        treasureRunRecorderObserver=new MutationObserver(()=>{
          treasureRunRecorderUpdateButton();
          treasureRunRecorderScheduleSnapshot('mutation',450);
        });
        treasureRunRecorderObserver.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class','style','data-lot-id']});
      }
"""
new_obs="""      if(!treasureRunRecorderObserver){
        treasureRunRecorderObserver=new MutationObserver(mutations=>{
          const relevant=mutations.some(mutation=>{
            const target=mutation.target instanceof Element
              ? mutation.target
              : mutation.target?.parentElement;
            return !target?.closest?.('#hkTreasureRunRecorderToggle');
          });
          if(!relevant)return;
          treasureRunRecorderLastMutationAt=Date.now();
          treasureRunRecorderUpdateButton();
          treasureRunRecorderScheduleSnapshot('mutation',450);
        });
        treasureRunRecorderObserver.observe(document.body,{
          childList:true,
          subtree:true,
          characterData:true,
          attributes:true,
          attributeFilter:['class','data-lot-id','disabled','aria-disabled','aria-busy']
        });
      }
"""
rep(old_obs,new_obs,"observer self-loop fix")

# Export new revision.
rep(
    """      revision:HK_TREASURE_RUN_RECORDER_REV,
      start:treasureRunRecorderStart,
""",
    """      revision:HK_TREASURE_RUN_RECORDER_REV,
      stabilityRevision:HK_TREASURE_RUN_RECORDER_STABILITY_REV,
      start:treasureRunRecorderStart,
""",
    "export recorder stability"
)

for marker in [
    "// @version      1.18.14",
    "const BUILD_VERSION = '1.18.14';",
    "treasure-run-recorder-stability-blockers-20260926-r2",
    "function treasureRunRecorderBlockingSignals()",
    "blocked-action",
    "no-state-change",
    "http-409-conflict",
    "http-429-rate-limit",
    "http-5xx-server-error",
    "attributeFilter:['class','data-lot-id','disabled','aria-disabled','aria-busy']",
    "treasureRunRecorderButton.textContent!==label",
    "return !target?.closest?.('#hkTreasureRunRecorderToggle')",
    "treasure-run-recorder-20260926-r1",
    "battle-visible-board-active-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "attributeFilter:['class','style','data-lot-id']" in s:
    raise SystemExit("unsafe style observer still present")

target.write_text(s,encoding="utf-8")
print("TREASURE_RUN_RECORDER_STABILITY_1_18_14=PASS")
