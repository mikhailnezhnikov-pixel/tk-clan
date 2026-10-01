"""Add only an isolated route dispatcher; preserve all existing handler bodies."""
import ast
import sys
from pathlib import Path

path=Path(sys.argv[1])
source=path.read_text()
marker='# TK_CONTEST_V1'
if marker in source:
    print('CONTEST_DISPATCH_ALREADY_INSTALLED')
    raise SystemExit(0)
tree=ast.parse(source)
handler=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Handler')
lines=source.splitlines(keepends=True)
changes=[]
for name in ('do_GET','do_POST'):
    method=next(n for n in handler.body if isinstance(n,ast.FunctionDef) and n.name==name)
    first=method.body[0]
    if isinstance(first,ast.Expr) and isinstance(first.value,ast.Constant) and isinstance(first.value.value,str):
        line=first.end_lineno
    else:
        line=first.lineno-1
    changes.append((line,'        if _tk_contest_dispatch(self):\n            return\n'))
changes.append((handler.lineno-1,marker+'\nfrom contest_runtime import install as _tk_install_contest\n_tk_contest_dispatch = _tk_install_contest(globals())\n\n'))
for index,value in sorted(changes,reverse=True):
    lines.insert(index,value)
result=''.join(lines)
ast.parse(result)
# Verify original methods still occur verbatim after removing the inserted guards.
clean=result.replace('        if _tk_contest_dispatch(self):\n            return\n','')
for name in ('do_GET','do_POST'):
    method=next(n for n in handler.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert ast.get_source_segment(source,method) in clean, 'Original handler changed'
path.write_text(result)
print('CONTEST_DISPATCH_PATCH=PASS; existing handlers preserved')
