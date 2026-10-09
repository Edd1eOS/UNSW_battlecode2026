"""A worker must not occupy its Queen's sole remaining exit."""
import importlib.util,json,re
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
raw=packet.frame(3,[(6,4),(7,4)],round_num=150,units=3,enemies=[(0,[(5,5),(4,5)])],
 edges=[((5,5),(6,5)),((6,4),(6,5)),((6,5),(7,5)),((7,5),(7,6)),((7,6),(8,6)),((8,6),(8,5)),((8,5),(7,5))])
raw=raw.replace('B 0 ','A 0 ');rows=[]
for name in ['v145-queen-early-brood','v174-preserve-queen-exits']:
 wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key='queen-exit-'+name)
 bot=SandboxBot(pool,init=b'ID 3\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',name='3')
 try:out=bot.ask(raw.encode()).decode();rows.append({'candidate':name,'source_sha256':digest,'output':out,'points':bot.live[0]})
 finally:bot.stop();pool.close()
assert 'MOVE S\n' in rows[0]['output'],rows
assert 'MOVE E\n' in rows[1]['output'],rows
(ROOT/'test-results/oct8-sprint/queen-exit-regression.json').write_text(json.dumps({'passed':True,'input':raw,'rows':rows},indent=2))
print(json.dumps({'passed':True,'rows':rows}))
