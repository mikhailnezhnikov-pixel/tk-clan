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

rep("// @version      1.17.94",
    "// @version      1.17.95\n"
    "// @release-note Ресурсы: «Выполнить рассчитанный максимум» теперь запускает уже рассчитанный обмен сразу, без второго системного confirm. Сообщение «Ресурсный обмен отменён пользователем» остаётся только для ручного режима с лимитом, если пользователь действительно отменил подтверждение.",
    "version")
rep("const BUILD_VERSION = '1.17.94';","const BUILD_VERSION = '1.17.95';","build")

anchor="  const HK_RESOURCE_KOKKARAS_CANON_REV='resources-kokkaras-5.3.22-20260925-r1';"
rep(anchor,anchor+"\n  const HK_RESOURCE_MAXIMUM_DIRECT_RUN_REV='resource-maximum-direct-run-20260925-r1';","direct run marker")

old=r'''      const lines=options.map((row,index)=>`${index+1}. ${resourceDisplayName(row)} ×${row.plannedCompletions.toLocaleString(locale())}`);
      const heading=maximumMode
        ? either('Выполнить рассчитанный максимальный обмен?','Run the calculated maximum exchange?')
        : either(`Выполнить ресурсные задания? Лимит ×${totalCompletions}.`,`Run resource tasks? Limit ×${totalCompletions}.`);
      if(!confirm(`${heading}\n\n${lines.join('\n')}`)){
        hkRunner.reset();
        log(either('Ресурсный обмен отменён пользователем.','Resource exchange cancelled by the user.'),'warn');
        return;
      }

      hkRunner.state.total=options.length;'''

new=r'''      if(!maximumMode){
        const lines=options.map((row,index)=>`${index+1}. ${resourceDisplayName(row)} ×${row.plannedCompletions.toLocaleString(locale())}`);
        const heading=either(`Выполнить ресурсные задания? Лимит ×${totalCompletions}.`,`Run resource tasks? Limit ×${totalCompletions}.`);
        if(!confirm(`${heading}\n\n${lines.join('\n')}`)){
          hkRunner.reset();
          log(either('Ресурсный обмен отменён пользователем.','Resource exchange cancelled by the user.'),'warn');
          return;
        }
      }else{
        log(either(
          'Ресурсы: рассчитанный максимум подтверждён кнопкой — запускаю обмен сразу.',
          'Resources: calculated maximum was confirmed by the button — starting exchange immediately.'
        ));
      }

      hkRunner.state.total=options.length;'''
rep(old,new,"maximum mode direct run")

for marker in [
    "// @version      1.17.95",
    "const BUILD_VERSION = '1.17.95';",
    "resource-maximum-direct-run-20260925-r1",
    "if(!maximumMode){",
    "рассчитанный максимум подтверждён кнопкой",
    "event_building_id:row.roomId",
    "number_of_completions:Number(quantity)",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
