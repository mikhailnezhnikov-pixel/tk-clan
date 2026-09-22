# HK Stage 2.11 — Growth / Развитие

## Status

**SOURCE_PREFLIGHT_PASS · CANONICAL_CURRENCY_BUG_CONFIRMED · PATCH_PREPARING**

## Pinned donor

Pinned donor confirmed from File Library and `reference/topking/REFERENCE.json`:

- Kokkaras HK Control Panel;
- donor version: `5.3.22-ui-icons-pit-dim`;
- exact donor Growth/Hamsters-Generals logic inspected before current baseline.

Relevant donor behavior:
- Hamster budget uses `cur_nut`;
- setting is `nutsPercent`;
- Hamster optimization logs and efficiency are Nuts / Power;
- General budget remains `item_pit_token`;
- default copy priority is the same 12-pair list already present in HK;
- preparation order remains contracts → balls → boxes.

## Current baseline

- userscript: `1.17.35`;
- Growth current implementation uses:
  - `GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'`;
  - saved setting `capsPercent`;
  - UI label `Caps budget`;
  - Hamster cost guard only allows the value of `GROWTH_HAMSTER_BUDGET_ID`;
  - Hamster level efficiency is therefore currently calculated as Caps / Power.

The wrong currency has existed since the older HK 1.17.4 Growth transfer, so this is a long-lived transfer regression rather than a recent change.

## Confirmed bug

Donor:
- `hgRunHamsters(...)` starts from `panelResourceQuantity(state,'cur_nut')`;
- budget is `settings.nutsPercent`;
- spend tracking uses Nut cost.

Current HK:
- starts from `cur_cap`;
- budget is `settings.capsPercent`;
- safe cost filtering accepts only Caps;
- level efficiency and budget limit use Caps.

Impact:
- valid Hamster upgrades paid in Nuts may be filtered out;
- budget ceiling can be calculated from the wrong wallet;
- the full Growth plan can skip or mis-rank Hamster actions;
- labels falsely report Caps.

**CANONICAL CURRENCY BUG: CONFIRMED**

## Planned 1.17.36 correction

- `GROWTH_HAMSTER_BUDGET_ID: cur_cap → cur_nut`;
- `capsPercent → nutsPercent`;
- migrate existing saved `capsPercent` value into the new Nuts percentage when `nutsPercent` is absent;
- rename Growth cost helper semantics from Cap to Nut;
- Hamster budget UI becomes Nuts;
- efficiency becomes Nuts / Power;
- summary keeps separate Caps and Nuts balances;
- General/Pit Token logic remains unchanged;
- no actual Growth mutation is executed by CI.

## Safety invariants

Preserve:
- fail-closed Auto Routines 1.17.34;
- Auto Routines embedded in Today 1.17.35;
- adaptive 429 guard;
- collector activity lease;
- Clan Shop current revision;
- Kokkaras Businesses canon;
- mutation requests with generic retry disabled.

## Browser gate after technical deploy

1. open **Развитие**;
2. confirm summary shows separate Caps and Nuts;
3. open **Хомяки**;
4. confirm budget says **Орехи / Nuts**, not Caps;
5. confirm saved percentage is preserved;
6. do not run a destructive plan until the displayed budget and live Nut balance look correct.

Stage 2.12 Hamsters and Stage 2.13 Generals remain separate live-action checks after Growth overview/full-plan parity is restored.
