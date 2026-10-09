"""A trapped worker facing a friendly Queen must not take both dragons down."""
import importlib.util,json,re
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py')
packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
raw=packet.frame(2,[(5,5),(5,4)],round_num=100,units=2,enemies=[(0,[(5,6),(4,6)])],edges=[((5,5),(5,6))])
raw=raw.replace('B 0 ','A 0 ')
rows=[]
for name in ['v114-evaluation-cache','v124-friendly-head-guard']:
    wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key=name)
    bot=SandboxBot(pool,init=b'ID 2\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',name='2')
    try:
        out=bot.ask(raw.encode()).decode();rows.append({'candidate':name,'source_sha256':digest,'output':out,'points':bot.live[0]})
    finally:bot.stop();pool.close()
assert 'MOVE S\n' in rows[0]['output']
assert 'MOVE S\n' not in rows[1]['output']
assert re.search(r'^MOVE [NEW]$',rows[1]['output'],re.M)
(ROOT/'test-results/oct8-sprint/friendly-queen-regression.json').write_text(json.dumps({'input':raw,'passed':True,'rows':rows},indent=2))
print(json.dumps({'passed':True,'rows':rows}))
