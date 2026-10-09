"""Targeted parent/newborn protocol observations for a late tail strike."""
import importlib.util,json
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
rows=[]
for name,identity,body in [('v145-queen-early-brood',4,[(8,8),(7,8),(6,8),(5,8)]),('v183-tail-worker-strike',4,[(8,8),(7,8),(6,8),(5,8)]),('v183-tail-worker-strike',5,[(5,8),(6,8)])]:
 raw=packet.frame(identity,body,round_num=450,units=4,enemies=[(0,[(5,7),(4,7)])])
 wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key='tail-strike-'+name+str(identity))
 bot=SandboxBot(pool,init=f'ID {identity}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n'.encode(),name=str(identity))
 try:out=bot.ask(raw.encode()).decode();rows.append({'candidate':name,'id':identity,'source_sha256':digest,'input':raw,'output':out,'points':bot.live[0]})
 finally:bot.stop();pool.close()
assert 'SPLIT 2\n' not in rows[0]['output'],rows
assert 'SPLIT 2\n' in rows[1]['output'],rows
assert 'MOVE N\n' in rows[2]['output'],rows
(ROOT/'test-results/oct8-sprint/tail-strike-regression.json').write_text(json.dumps({'passed':True,'scope':'isolated parent and newborn protocol decisions, not an entire engine game','rows':rows},indent=2))
print(json.dumps({'passed':True,'outputs':[r['output'] for r in rows]}))
