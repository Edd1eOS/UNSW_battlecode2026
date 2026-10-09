"""An unreachable Queen must not hide a reachable worker trade."""
import importlib.util,json
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py')
packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
raw=packet.frame(4,[(5,5),(4,5)],round_num=200,units=3,
    enemies=[(1,[(7,7),(7,6)]),(3,[(6,5),(6,6)])],
    edges=[((5,5),(6,5)),((5,5),(5,4)),((5,4),(4,4)),((4,4),(4,5))])
rows=[]
for name in ['v198-postmove-space','v218-reachable-attack-targets']:
    wasm,digest=build(ROOT/'opponents'/name)
    pool=WasmPool([str(wasm)],key='reachable-target-'+name)
    bot=SandboxBot(pool,init=b'ID 4\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',name=name)
    try:
        out=bot.ask(raw.encode()).decode();rows.append({'candidate':name,'source_hash':digest,'input':raw,'output':out,'points':bot.live[0],'error':bot.error})
    finally:bot.stop();pool.close()
assert 'MOVE E\n' not in rows[0]['output'],rows
assert 'MOVE E\n' in rows[1]['output'] and 'ATTACK_LARGE_WORKER' in rows[1]['output'],rows
assert not any(r['error'] for r in rows),rows
(ROOT/'test-results/oct8-sprint/reachable-target-regression.json').write_text(json.dumps({'passed':True,'scope':'Single legal local observation; decision regression, not a full strength game','rows':rows},indent=2),encoding='utf8')
print(json.dumps({'passed':True,'outputs':[r['output'] for r in rows]}))
