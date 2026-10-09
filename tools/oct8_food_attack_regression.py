"""A length-two worker can finance a three-step strike with two visible pearls."""
import importlib.util,json
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
raw=packet.frame(4,[(5,5),(4,5)],round_num=100,units=3,pearls=[(6,5),(7,5)],enemies=[(1,[(8,5),(8,4)])])
rows=[]
for name in ['v218-reachable-attack-targets','v241-food-funded-attacks']:
    wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key='food-strike-'+name)
    bot=SandboxBot(pool,init=b'ID 4\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',name='4')
    try:out=bot.ask(raw.encode()).decode();rows.append({'candidate':name,'source_sha256':digest,'output':out,'points':bot.live[0],'error':bot.error})
    finally:bot.stop();pool.close()
assert 'MOVE EEE\n' not in rows[0]['output'],rows
assert 'MOVE EEE\n' in rows[1]['output'] and not rows[1]['error'],rows
(ROOT/'test-results/oct8-sprint/food-attack-regression.json').write_text(json.dumps({'passed':True,'scope':'protocol decision; visible pearls finance two paid moves, no whole-match counterfactual','input':raw,'rows':rows},indent=2))
print(json.dumps({'passed':True,'outputs':[r['output'] for r in rows]}))
