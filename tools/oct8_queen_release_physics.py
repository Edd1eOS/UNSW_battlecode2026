"""A trapped Queen's last exit can be released by a blocking worker."""
import json,re,hashlib
from pathlib import Path
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS
from unswbc.sandbox import SandboxBot,WasmPool
from verify_candidate import build
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'test-results/oct8-sprint/queen-release-physics';out.mkdir(exist_ok=True)
raw=('MAP 20 20\nMAP_NAME Trapped Queen release\nTILE_COUNT 0\nEDGE_COUNT 2\nEDGE 236 1 -1\nEDGE 257 1 -1\nDRAGON_COUNT 5\n'
     'DRAGON 0 2 5 4 4 4\nDRAGON 1 2 17 17 18 17\nDRAGON 0 2 6 5 7 5\nDRAGON 1 2 12 17 13 17\nDRAGON 0 2 17 12 18 12\n').encode()
rows=[]
for name in ['v218-reachable-attack-targets','v240-release-trapped-queen']:
    wasm,digest=build(ROOT/'opponents'/name);pool=WasmPool([str(wasm)],key='release-physics-'+name);bots={};frames=[];deaths=[];notices=[];seen=[]
    def spawn(i,init):
        if i==2:bots[i]=SandboxBot(pool,init=init,name=str(i))
    def reply(i,block):
        rnd=int(re.search(rb'^ROUND (\d+)',block,re.M)[1]);length=int(re.search(rb'^LENGTH (\d+)',block,re.M)[1]);seen.append({'id':i,'round':rnd,'length':length})
        if rnd>=2:return b'ENDTURN\n'
        if i==0:return (b'MOVE S\nENDTURN\n' if rnd==0 else b'MOVE E\nENDTURN\n')
        if i!=2:return b'MOVE N\nENDTURN\n'
        bot=bots[i];answer=bot.ask(block);frames.append({'round':rnd,'input':block.decode(),'output':answer.decode(),'error':bot.error,'points':bot.live[0]});return answer+b'ENDTURN\n'
    engine=EngineModule()
    try:
        engine.run(raw,reply,bot_spawn=spawn,on_death=lambda i,r,reason:deaths.append({'id':i,'round':r,'reason':reason}),on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100884)
        replay=engine.replay('candidate-worker-A','fixed-B');(out/f'{name}.replay').write_bytes(replay)
    finally:
        for bot in bots.values():bot.stop()
        pool.close()
    rows.append({'candidate':name,'source_sha256':digest,'frames':frames,'deaths':deaths,'seen':seen,'notices':notices,'replay_sha256':hashlib.sha256(replay).hexdigest()})
assert any(d['id']==0 and d['round']==1 and d['reason']=='O' for d in rows[0]['deaths']),rows
assert any(d['id']==2 and d['round']==0 and d['reason']=='S' for d in rows[1]['deaths']),rows
assert any(s=={'id':0,'round':2,'length':3} for s in rows[1]['seen']),rows
assert all(not r['notices'] and all(not f['error'] for f in r['frames']) for r in rows),rows
(out/'result.json').write_text(json.dumps({'passed':True,'scope':'two-turn official-engine integration with fixed other dragons; deliberate stop round2; not a strength match','map':raw.decode(),'rows':rows},indent=2))
print(json.dumps({'passed':True,'outputs':[r['frames'][0]['output'] for r in rows]}))
