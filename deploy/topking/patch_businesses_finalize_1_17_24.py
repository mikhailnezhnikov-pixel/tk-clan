from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def require(marker, label=None):
    if marker not in s:
        raise SystemExit("missing expected marker: " + (label or marker[:180]))

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s = s.replace(old, new, 1)

for marker in [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';",
    "async function executeBusinessPlan()",
    "playerDocument = await hkAuthoritativePlayerRead('business-complete');",
    "hkRunner.finish(either('Перестановка завершена','Rearrangement completed'));",
]:
    require(marker)

replace_once(
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "const HK_CORE_REVISION = 'core-20260921-r28-businesses-finalize';",
    "core revision"
)

replace_once(
    "const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';",
    "const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';\n  const HK_BUSINESSES_FINALIZE_REV='businesses-finalize-single-snapshot-20260921-r1';",
    "finalize marker"
)

old_insert = """      for (const [row, id] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), inserted.length, Math.max(1,plan.length));
        if (!id) { log(`${either('Оставляю пустым','Leaving empty')}: ${buildingSlotLabel(row)}`); continue; }
        log(`Вставляю T${tier(id)}…`);
        const response = await businessAction('insert', row, id); inserted.push([row,id]);
        const state = findSlot(response, row.buildingId, row.slot);
        if (!state) throw new Error('После вставки сервер не вернул новый бизнес');
        if (state.businessId !== id) throw new Error(either('Сервер вернул другой бизнес после вставки', 'The server returned a different business after insertion'));
        await finishPendingBusiness(state, `T${tier(id)}`, true);
      }
      // Do not announce completion until every inserted business, including the
      // last one, is confirmed ACTIVE by /player/me.
      for (const [row, id] of inserted) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        let state = await readBusinessSlot(row.buildingId, row.slot,
          value => businessSlotIsActive(value, id), 6);
        if (!businessSlotIsActive(state, id)) {
          if (!state || state.businessId !== id) throw new Error(either(
            `Последний контроль: в слоте отсутствует вставленный T${tier(id)}`,
            `Final check: inserted T${tier(id)} is missing from its slot`));
          await finishPendingBusiness(state, `T${tier(id)}`, true);
          state = await readBusinessSlot(row.buildingId, row.slot,
            value => businessSlotIsActive(value, id), 6);
        }
        if (!businessSlotIsActive(state, id)) throw new Error(either(
          `Последний контроль: T${tier(id)} не активирован`,
          `Final check: T${tier(id)} is not active`));
      }
      playerDocument = await hkAuthoritativePlayerRead('business-complete');
      refreshBusinessData();
      hkRunner.finish(either('Перестановка завершена','Rearrangement completed'));"""

new_insert = """      let processedInsertRows = 0;
      for (const [row, id] of plan) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), processedInsertRows, Math.max(1,plan.length));
        if (!id) {
          log(`${either('Оставляю пустым','Leaving empty')}: ${buildingSlotLabel(row)}`);
          processedInsertRows += 1;
          hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), processedInsertRows, Math.max(1,plan.length));
          continue;
        }
        log(`Вставляю T${tier(id)}…`);
        const response = await businessAction('insert', row, id); inserted.push([row,id]);
        const state = findSlot(response, row.buildingId, row.slot);
        if (!state) throw new Error('После вставки сервер не вернул новый бизнес');
        if (state.businessId !== id) throw new Error(either('Сервер вернул другой бизнес после вставки', 'The server returned a different business after insertion'));
        await finishPendingBusiness(state, `T${tier(id)}`, true);
        processedInsertRows += 1;
        hkRunner.setStep(either('Вставляю бизнесы','Inserting businesses'), processedInsertRows, Math.max(1,plan.length));
      }

      // All mutation rows have been processed. Use one authoritative snapshot
      // for the normal final check instead of rereading /player/me once per slot.
      // Only slots that are genuinely unresolved get a targeted recovery read.
      hkRunner.setStep(either('Проверяю результат','Verifying result'), Math.max(1,plan.length), Math.max(1,plan.length));
      playerDocument = await hkAuthoritativePlayerRead('business-final-check');

      let unresolved = inserted.filter(([row, id]) =>
        !businessSlotIsActive(findSlot(playerDocument, row.buildingId, row.slot), id));

      for (const [row, id] of unresolved) {
        if (hkRunner.signal?.aborted) throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        let state = findSlot(playerDocument, row.buildingId, row.slot);
        if (!state || state.businessId !== id) throw new Error(either(
          `Последний контроль: в слоте отсутствует вставленный T${tier(id)}`,
          `Final check: inserted T${tier(id)} is missing from its slot`));
        await finishPendingBusiness(state, `T${tier(id)}`, true);
        state = await readBusinessSlot(row.buildingId, row.slot,
          value => businessSlotIsActive(value, id), 3);
        if (!businessSlotIsActive(state, id)) throw new Error(either(
          `Последний контроль: T${tier(id)} не активирован`,
          `Final check: T${tier(id)} is not active`));
      }

      unresolved = inserted.filter(([row, id]) =>
        !businessSlotIsActive(findSlot(playerDocument, row.buildingId, row.slot), id));
      if (unresolved.length) throw new Error(either(
        `Последний контроль не подтверждён для ${unresolved.length} бизнесов`,
        `Final verification was not confirmed for ${unresolved.length} businesses`));

      refreshBusinessData();
      hkRunner.finish(either('Перестановка завершена','Rearrangement completed'));"""

replace_once(old_insert, new_insert, "business finalization block")

# Keep the completed Businesses state visible long enough for the user to see it.
old_finish = """      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); const exploreTitle=[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(String(state.title||'')); const keep=exploreTitle?15000:1800; setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},keep); },"""
new_finish = """      finish(step='') { if(step)state.step=String(step); state.status='done'; if(state.total)state.done=state.total; recordDiagnostic('runner-finish',{title:state.title}); emit(); const title=String(state.title||''),exploreTitle=[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),businessesTitle=title===either('Перестановка бизнесов','Business rearrangement'); const keep=exploreTitle?15000:businessesTitle?6000:1800; setTimeout(()=>{if(state.status==='done'){state.status='idle';emit();}},keep); },"""
replace_once(old_finish, new_finish, "business completion visibility")

for marker in [
    "const HK_CORE_REVISION = 'core-20260921-r28-businesses-finalize';",
    "const HK_BUSINESSES_FINALIZE_REV='businesses-finalize-single-snapshot-20260921-r1';",
    "let processedInsertRows = 0;",
    "hkRunner.setStep(either('Проверяю результат','Verifying result'), Math.max(1,plan.length), Math.max(1,plan.length));",
    "playerDocument = await hkAuthoritativePlayerRead('business-final-check');",
    "let unresolved = inserted.filter",
    "businessesTitle?6000:1800",
    "businesses-rearrange-desktop-safe-t123-20260921-r1",
    "businesses-runner-canon-20260921-r1",
    "businesses-catalog-readonly-20260921-r1",
    "function businessRemovalAllowed(",
    "assertBusinessRemovalPlanAllowed",
]:
    require(marker, "post-patch " + marker)

# The old O(N) final verification loop must be gone from executeBusinessPlan.
business_block = s[s.index("  async function executeBusinessPlan()"):s.index("  function prepareOriginalBusinessRestore()")]
if "last one, is confirmed ACTIVE by /player/me" in business_block:
    raise SystemExit("legacy per-slot final verification comment still present")
if "value => businessSlotIsActive(value, id), 6" in business_block:
    raise SystemExit("legacy six-attempt per-slot final reread still present")

PATH.write_text(s, encoding="utf-8")
print("BUSINESSES_FINALIZE_SINGLE_SNAPSHOT_R1_PATCH=PASS")
