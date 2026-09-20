from pathlib import Path

p = Path('/tmp/HamsterKingMobile.user.js')
s = p.read_text(encoding='utf-8')

marker = "const HK_TODAY_CANON_FILTER_REV = 'today-kokkaras-filter-20260920-r2';"
if marker in s:
    raise SystemExit('r2 already applied')
anchor = "  const HK_TODAY_CANON_REV = 'today-kokkaras-order-20260920-r1';\n"
if anchor not in s:
    raise SystemExit('r1 marker missing')
s = s.replace(anchor, anchor + "  " + marker + "\n", 1)

helper_anchor = "  function dailyActionRows() {\n"
if helper_anchor not in s:
    raise SystemExit('dailyActionRows missing')
helper = r'''  function dailyCanonEventRegularRows() {
    const tabs = dailyClientConfigDocument?.event?.tabs || [];
    let activeTab = String(tabs.find(tab => String(tab?.type || '') === 'shop' && tab?.tab)?.tab || '');
    if (!activeTab) {
      const fallback = tabs.find(tab => String(tab?.type || '') === 'quests' && String(tab?.zone || '').startsWith('event_'));
      activeTab = String(fallback?.zone || '');
    }
    if (!activeTab) return [];

    const normalized = new Map(dailyShopRows.map(row => [String(row?.lotId || ''), row]));
    const lots = Array.isArray(shopViewDocument?.shop_lots) ? shopViewDocument.shop_lots : [];
    return lots.filter(lot => {
      if (!lot?.id) return false;
      const view = lot?.lot_view || {};
      if (String(view?.tab || '') !== activeTab) return false;
      if (String(view?.type || '').toLowerCase() === 'hidden') return false;
      if (lot?.is_ad === true || lot?.external_cost) return false;
      if (!String(view?.group || '').toLowerCase().includes('event_repeatable_daily_offers')) return false;
      if ((lot?.cost?.currencies || []).some(row => ['cur_prem','cur_hard'].includes(String(row?.id || '')))) return false;
      const limits = (lot?.limit || []).filter(row =>
        String(row?.type || '').toUpperCase() === 'PLAYER' &&
        String(row?.reset_type || '').toUpperCase() === 'DAILY'
      );
      if (!limits.length) return false;
      const total = Math.max(0, ...limits.map(row => Math.max(0, Number(row?.limit || 0) + Number(row?.bonus || 0))));
      return total > 0;
    }).sort((a,b) => Number(b?.priority || 0) - Number(a?.priority || 0))
      .map(lot => normalized.get(String(lot.id || '')))
      .filter(row => row?.safe);
  }

'''
s = s.replace(helper_anchor, helper + helper_anchor, 1)

old = "    rows.filter(x=>x.section==='regular').forEach(x=>push(x,'event'));"
new = "    dailyCanonEventRegularRows().forEach(x=>push(x,'event'));"
if old not in s:
    raise SystemExit('event rows anchor missing')
s = s.replace(old, new, 1)

s = s.replace(
    "label:either('Награды рейтинга: Ямы / Боссы / Крысы','Leaderboard rewards: Pits / Bosses / Rats')",
    "label:either('Собрать награды рейтинга: Ямы / Боссы / Крысы','Claim leaderboard rewards: Pits / Bosses / Rats')",
    1
)
s = s.replace(
    "label:either('Battle Pass боссов — получить награды','Area Boss Battle Pass — claim rewards')",
    "label:either('Собрать награды Battle Pass боссов','Claim Area Boss Battle Pass rewards')",
    1
)

for needle in [
    marker,
    "event_repeatable_daily_offers",
    "reset_type || '').toUpperCase() === 'DAILY'",
    "dailyCanonEventRegularRows().forEach",
    "Собрать награды рейтинга",
    "Собрать награды Battle Pass боссов"
]:
    if needle not in s:
        raise SystemExit('missing invariant: ' + needle)

p.write_text(s, encoding='utf-8')
print('TODAY_CANON_FILTER_R2_OK')
