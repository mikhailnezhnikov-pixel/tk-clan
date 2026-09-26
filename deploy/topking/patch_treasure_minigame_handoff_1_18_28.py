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

rep("// @version      1.18.27",
    "// @version      1.18.28\n// @release-note Карта Сокровищ: исправлены три перехода мини-игр по записи прохода #5. Сражение теперь забирает реальный Сундук победителя (mf_fairlot_minigame_fight_room_big_chest) и после награды передаёт управление Автокарте; Лабиринт/лампочки забирают mf_fairlot_lights_out_reward_slot до перехода в следующую комнату; Рыбалка использует фактические «забросы» из mf_treasurelot_fishing_rod_* как бюджет и больше не выходит при наличии попыток.\n// @release-note Мини-игры: мобильный tap больше не генерирует два click подряд. Убрано дублирование synthetic click + element.click(), которое вызывало лишние 409 Shop lot cannot be bought.",
    "version")
rep("const BUILD_VERSION = '1.18.27';",
    "const BUILD_VERSION = '1.18.28';",
    "build")
rep("  const HK_BATTLE_FULL_CLEAR_EXIT_REV='battle-full-clear-exit-20260927-r1';",
    "  const HK_BATTLE_FULL_CLEAR_EXIT_REV='battle-full-clear-exit-20260927-r1';\n  const HK_TREASURE_FINAL_REWARD_HANDOFF_REV='treasure-final-reward-handoff-20260927-r1';\n  const HK_FISHING_VISIBLE_CASTS_REV='fishing-visible-casts-20260927-r1';\n  const HK_MINIGAME_SINGLE_TAP_REV='minigame-single-tap-20260927-r1';",
    "revisions")

# One logical tap must create one click event. Pointer/mouse down/up are retained
# for the mobile game, but the synthetic click + .click() double-fire is removed.
rep("""      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('click',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_BATTLE_VICTORY_TAP_REV,label,x:Math.round(x),y:Math.round(y),tag:leaf.tagName||''});
""",
"""      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_MINIGAME_SINGLE_TAP_REV,label,x:Math.round(x),y:Math.round(y),tag:leaf.tagName||''});
""",
"single tap element")

rep("""      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.dispatchEvent(new MouseEvent('click',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_BATTLE_VICTORY_TAP_REV,label,x:Math.round(px),y:Math.round(py),tag:leaf.tagName||''});
""",
"""      try { leaf.dispatchEvent(new MouseEvent('mouseup',{...options,buttons:0})); } catch (_) {}
      try { leaf.click?.(); } catch (_) {}
      recordDiagnostic('battle-mobile-tap',{revision:HK_MINIGAME_SINGLE_TAP_REV,label,x:Math.round(px),y:Math.round(py),tag:leaf.tagName||''});
""",
"single tap coordinates")

# Fishing attempts are not a normal wallet resource. The live rod tile is the
# authoritative remaining-attempt counter (e.g. mf_treasurelot_fishing_rod_03_12).
anchor="""    function fishingAffordable(cost) {
"""
if s.count(anchor)!=1:
    raise SystemExit("fishing affordable anchor missing")
helper="""    function fishingVisibleCasts() {
      const rods=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_fishing_rod_"]')].filter(visible);
      for (const element of rods) {
        const lotId=String(element.getAttribute('data-lot-id')||'');
        const byId=lotId.match(/mf_treasurelot_fishing_rod_\\d+_(\\d+)/);
        if (byId) return Math.max(0,Number(byId[1])||0);
        const text=clean(element.innerText||element.textContent||'');
        const byText=text.match(/(\\d+)\\s*(?:заброс(?:ов|а)?|casts?)/i);
        if (byText) return Math.max(0,Number(byText[1])||0);
      }
      const body=clean(document.body?.innerText||'');
      const byBody=body.match(/(\\d+)\\s*(?:заброс(?:ов|а)?|casts?)/i);
      return byBody ? Math.max(0,Number(byBody[1])||0) : null;
    }

"""
s=s.replace(anchor,helper+anchor,1)

old_aff="""    function fishingAffordable(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      const id=String(cost?.id||'');
      if (!(quantity>0) || !id) return false;
      const amount=walletAmount(id);
      return amount!==null && Number(amount)>=quantity;
    }

    function fishingBudgetSnapshot(cost) {
      const id=String(cost?.id||'');
      const amount=id ? walletAmount(id) : null;
      return {
        id,
        balance:amount===null ? null : Number(amount),
        cost:Math.max(0,Number(cost?.quantity||0))
      };
    }
"""
new_aff="""    function fishingAffordable(cost) {
      const quantity=Math.max(0,Number(cost?.quantity||0));
      if (!(quantity>0)) return false;

      const casts=fishingVisibleCasts();
      if (casts!==null) return casts>=quantity;

      const id=String(cost?.id||'');
      if (!id) return false;
      const amount=walletAmount(id);
      return amount!==null && Number(amount)>=quantity;
    }

    function fishingBudgetSnapshot(cost) {
      const id=String(cost?.id||'');
      const amount=id ? walletAmount(id) : null;
      const casts=fishingVisibleCasts();
      return {
        id,
        balance:casts!==null ? casts : (amount===null ? null : Number(amount)),
        casts,
        source:casts!==null ? 'visible-rod' : (amount===null ? 'unknown' : 'wallet'),
        cost:Math.max(0,Number(cost?.quantity||0))
      };
    }
"""
rep(old_aff,new_aff,"fishing visible budget")

rep("""    function fishingSignature() {
      return 'FISHING|'+fishingElements()
""",
"""    function fishingSignature() {
      return 'FISHING|casts='+String(fishingVisibleCasts())+'|'+fishingElements()
""",
"fishing signature casts")

# The actual battle reward observed in run #5 is a dedicated big-chest lot.
# Dead enemy tiles are not the claim target.
old_battle="""    function battleVictoryElement() {
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_defeated"]')].filter(visible);
      return elements
        .map(element=>({element,area:(element.getBoundingClientRect?.().width||0)*(element.getBoundingClientRect?.().height||0)}))
        .sort((a,b)=>b.area-a.area)[0]?.element || null;
    }
"""
new_battle="""    function battleVictoryElement() {
      const exact=[...document.querySelectorAll('[data-lot-id="mf_fairlot_minigame_fight_room_big_chest"]')]
        .find(element=>visible(element));
      if (exact) return exact;

      // Compatibility fallback for older layouts: only a defeated tile with an
      // explicit action marker may be treated as the final reward.
      const elements=[...document.querySelectorAll('[data-lot-id*="mf_treasurelot_enemy_defeated"]')].filter(visible);
      return elements
        .filter(element=>/▷|▶|►|claim|collect|забрать|получить/i.test(clean(element.innerText||element.textContent||'')))
        .map(element=>({element,area:(element.getBoundingClientRect?.().width||0)*(element.getBoundingClientRect?.().height||0)}))
        .sort((a,b)=>b.area-a.area)[0]?.element || null;
    }
"""
rep(old_battle,new_battle,"battle victory exact lot")

rep("""        const success=!battleVictoryModalRoot();
        recordDiagnostic('battle-victory-claim-complete',{revision:HK_BATTLE_VICTORY_TAP_REV,success});
        return success;
""",
"""        const success=!battleVictoryModalRoot();
        recordDiagnostic('battle-victory-claim-complete',{
          revision:HK_TREASURE_FINAL_REWARD_HANDOFF_REV,
          success,
          lotId:'mf_fairlot_minigame_fight_room_big_chest'
        });
        if (success && autoMapEnabled()) {
          setTimeout(()=>void runAutoMapTick('battle-victory-claimed'),minigameRandomMs(700,1200));
        }
        return success;
""",
"battle reward automap handoff")

# Once the last lamp purchase resolves, the board is replaced by eight inert
# slots + mf_fairlot_lights_out_reward_slot. Claim it before treating the board
# as closed / allowing AutoMap to reroll out of the room.
old_invalid="""          const board=getLightsBoard();
          const valid=board.filter(cell=>cell!==null);
          if (valid.length!==9) {
            if (!getSignature().startsWith('LIGHTS|')) {
              clearNumbers();
              recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_AUTO_REV,steps,reason:'board-closed'});
              return true;
            }
            return failLightsAuto('board-invalid',{valid:valid.length,steps});
          }
"""
new_invalid="""          const board=getLightsBoard();
          const valid=board.filter(cell=>cell!==null);
          if (valid.length!==9) {
            if (lightsRewardElement()) {
              const rewardResult=await runLightsFinalReward(runId,steps);
              if (!rewardResult.ok) {
                if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
                return failLightsAuto(rewardResult.reason,{steps,phase:'post-board-replacement'});
              }
              recordDiagnostic('lights-auto-complete',{
                revision:HK_TREASURE_FINAL_REWARD_HANDOFF_REV,
                steps,
                reason:rewardResult.claimed?'post-board-reward-claimed':'post-board-solved'
              });
              if (rewardResult.claimed && autoMapEnabled()) {
                setTimeout(()=>void runAutoMapTick('lights-final-reward-claimed'),minigameRandomMs(700,1200));
              }
              return true;
            }
            if (!getSignature().startsWith('LIGHTS|')) {
              clearNumbers();
              recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_AUTO_REV,steps,reason:'board-closed'});
              return true;
            }
            return failLightsAuto('board-invalid',{valid:valid.length,steps});
          }
"""
rep(old_invalid,new_invalid,"lights post-board reward")

# Preserve the final reward as a LIGHTS signature so checkPuzzle/AutoMap do not
# misclassify the room as complete during the handoff.
rep("""    function getSignature() {
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')].filter(visible);
""",
"""    function getSignature() {
      const lightsReward=lightsRewardElement();
      if (lightsReward) return 'LIGHTS|REWARD|mf_fairlot_lights_out_reward_slot';
      const lights = [...document.querySelectorAll('[data-lot-id^="mf_fairlot_lights_out_sl"]')].filter(visible);
""",
"lights reward signature")

rep("""      } else if (signature.startsWith('LIGHTS|')) {
        elements=getLightsBoard().filter(Boolean).map(cell=>cell.element).filter(Boolean);
""",
"""      } else if (signature.startsWith('LIGHTS|')) {
        elements=getLightsBoard().filter(Boolean).map(cell=>cell.element).filter(Boolean);
        const reward=lightsRewardElement();
        if (reward) elements.push(reward);
""",
"lights reward foreground")

rep("      battleFullClearExitRevision:HK_BATTLE_FULL_CLEAR_EXIT_REV,\n      start,",
    "      battleFullClearExitRevision:HK_BATTLE_FULL_CLEAR_EXIT_REV,\n      treasureFinalRewardHandoffRevision:HK_TREASURE_FINAL_REWARD_HANDOFF_REV,\n      fishingVisibleCastsRevision:HK_FISHING_VISIBLE_CASTS_REV,\n      minigameSingleTapRevision:HK_MINIGAME_SINGLE_TAP_REV,\n      start,",
    "export revisions")

for marker in [
    "// @version      1.18.28",
    "const BUILD_VERSION = '1.18.28';",
    "treasure-final-reward-handoff-20260927-r1",
    "fishing-visible-casts-20260927-r1",
    "minigame-single-tap-20260927-r1",
    "mf_fairlot_minigame_fight_room_big_chest",
    "mf_fairlot_lights_out_reward_slot",
    "function fishingVisibleCasts()",
    "source:casts!==null ? 'visible-rod'",
    "battle-victory-claimed",
    "lights-final-reward-claimed",
    "battle-full-clear-exit-20260927-r1",
    "minigame-human-pacing-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_MINIGAME_HANDOFF_1_18_28=PASS")
