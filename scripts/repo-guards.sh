#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 - <<'PY'
import ast,pathlib,json
root=pathlib.Path('.')
for p in (root/'src').rglob('*.py'):
    tree=ast.parse(p.read_text())
    for n in ast.walk(tree):
        if isinstance(n,ast.Call):
            if any(k.arg=='shell' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords):
                raise SystemExit(f'Forbidden shell=True: {p}')
            if isinstance(n.func,ast.Attribute):
                owner = n.func.value.id if isinstance(n.func.value,ast.Name) else ''
                if n.func.attr == 'rmtree' or (owner == 'os' and n.func.attr in {'system','popen'}):
                    raise SystemExit(f'Forbidden destructive/shell API: {p}')
        if 'domain' in p.parts and isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
            if any(x.startswith(('subprocess','textual','psutil','mlx','laya','jev_clean.infrastructure','jev_clean.application','jev_clean.ui')) for x in names):
                raise SystemExit(f'Domain dependency violation: {p}')
profile=json.loads((root/'.sectormap.json').read_text())
for sector in profile['sectors']:
    assert (root/profile['src_base']/sector['root']).is_dir(), sector
for required in ['README.md','SECURITY.md','LICENSE','skills/jev-clean/SKILL.md','docs/RESEARCH.md']:
    assert (root/required).is_file(),required
print('Architecture/safety guards passed (local profile validation; not remote Map-engine certification)')
PY
