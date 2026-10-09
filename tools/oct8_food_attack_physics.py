"""Execute the candidate's pearl-funded strike in the official engine."""
import json,re,hashlib
from pathlib import Path
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS
from unswbc.sandbox import SandboxBot,WasmPool
from verify_candidate import build
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'test-results/oct8-sprint/food-attack-physics';out.mkdir(exist_ok=True)
raw=('MAP 20 20\nMAP_NAME Pearl-funded strike\nTILE_COUNT 2\nTILE 6 5 1 1\nTILE 7 5 1 1\nEDGE_COUNT 0\nDRAGON_COUNT 5\n'
     'DRAGON 0 2 17 17 18 17\nDRAGON 1 2 8 6 8 7\nDRAGON 0 2 5 5 4 5\nDRAGON 1 2 12 17 13 17\nDRAGON 0 2 17 12 18 12\n').encode()
rows=[]
for name in ['v218-reachable-attack-targets','v241-food-funded-attacks']:
    wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key='food-physics-'+name);bots={};frames=[];deaths=[];notices=[]
    def spawn(i,init):
        if i==2:bots[i]=SandboxBot(pool,init=init,name=str(i))
    def reply(i,block):
        rnd=int(re.search(rb'^ROUND (\d+)',block,re.M)[1])
        if rnd>=1:return b'ENDTURN\n'
        if i!=2:return b'MOVE N\nENDTURN\n'
        bot=bots[i];answer=bot.ask(block);frames.append({'input':block.decode(),'output':answer.decode(),'error':bot.error,'points':bot.live[0]});return answer+b'ENDTURN\n'
    engine=EngineModule()
    try:
        engine.run(raw,reply,bot_spawn=spawn,on_death=lambda i,r,reason:deaths.append({'id':i,'round':r,'reason':reason}),on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100882)
        replay=engine.replay('candidate-A','fixed-B');(out/f'{name}.replay').write_bytes(replay)
    finally:
        for bot in bots.values():bot.stop()
        pool.close()
    hit=any(d['id']==1 and d['round']==0 and d['reason']=='H' for d in deaths)
    rows.append({'candidate':name,'source_sha256':digest,'enemy_queen_hit':hit,'frames':frames,'deaths':deaths,'notices':notices,'replay_sha256':hashlib.sha256(replay).hexdigest()})
assert not rows[0]['enemy_queen_hit'] and rows[1]['enemy_queen_hit'],rows
assert all(not r['notices'] and all(not f['error'] for f in r['frames']) for r in rows),rows
(out/'result.json').write_text(json.dumps({'passed':True,'scope':'one-turn official-engine integration with fixed other dragons; deliberate stop round1; not a strength match','map':raw.decode(),'rows':rows},indent=2))
print(json.dumps({'passed':True,'outputs':[r['frames'][0]['output'] for r in rows]}))
