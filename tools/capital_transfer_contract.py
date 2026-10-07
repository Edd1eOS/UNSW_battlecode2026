"""Real two-turn intra-team delivery, versus fixed replies; not a strength game."""
import hashlib,json,re
from pathlib import Path
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS
from unswbc.sandbox import SandboxBot,WasmPool
from audit_online import load_replay

ROOT=Path(__file__).resolve().parents[1]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def main():
    panel=ROOT/'test-results/capital-transfer-v1-external';out=ROOT/'test-results/capital-transfer-contract';out.mkdir(exist_ok=True)
    freeze=json.loads((panel/'candidate/freeze.json').read_text());wasm=panel/'candidate/bot.wasm';assert digest(wasm.read_bytes())==freeze['wasm_sha256']
    raw=('MAP 20 20\nMAP_NAME Small donor contract\nTILE_COUNT 0\nEDGE_COUNT 2\nEDGE 215 1 -1\nEDGE 257 1 -1\nDRAGON_COUNT 5\n'
         'DRAGON 0 3 5 5 4 5 3 5\nDRAGON 1 2 17 17 18 17\nDRAGON 0 2 7 5 7 6\nDRAGON 1 2 17 12 18 12\nDRAGON 0 2 12 17 13 17\n').encode()
    pool=WasmPool([str(wasm)],key='capital-transfer-contract');bots={};frames=[];observed=[];notices=[]
    def spawn(i,init):
        if i in (0,2):bots[i]=SandboxBot(pool,init=init,name=str(i))
    def reply(i,block):
        rnd=int(re.search(rb'^ROUND (\d+)',block,re.M)[1]);length=int(re.search(rb'^LENGTH (\d+)',block,re.M)[1]);observed.append({'round':rnd,'id':i,'length':length})
        if rnd>=2:return b'LOG fixture finished intentionally\nENDTURN\n'
        if i not in bots:return b'MOVE N\nENDTURN\n'
        bot=bots[i];answer=bot.ask(block);stderr=bot.take_stderr().decode();points,memory=bot.live
        frames.append({'round':rnd,'id':i,'input':block.decode(),'output':answer.decode(),'error':bot.error,'stderr':stderr,'points':points,'framed':bot._framer.done})
        return answer+b'ENDTURN\n'
    engine=EngineModule()
    try:
        engine.run(raw,reply,bot_spawn=spawn,on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100785)
        replay=engine.replay('candidate-cooperation-A','fixed-replies-B');(out/'raw.replay').write_bytes(replay)
    finally:
        for bot in bots.values():bot.stop()
        pool.close()
    data=load_replay(out/'raw.replay',node_path='D:/node/node.exe')
    q0=next(f for f in frames if (f['round'],f['id'])==(0,0));d0=next(f for f in frames if (f['round'],f['id'])==(0,2));q1=next(f for f in frames if (f['round'],f['id'])==(1,0))
    death=next(e for e in data['events'] if e['type']=='dragonDeath' and e['id']==2)
    passed=('CAPITAL_OFFER donor=2' in q0['output'] and 'CAPITAL_RELEASE length=2' in d0['output'] and death['reason']=='S'
            and next(x['length'] for x in observed if (x['round'],x['id'])==(2,0))==4
            and not notices and all(not f['error'] and not f['stderr'] and f['framed'] and f['points']<90_000_000 for f in frames))
    result={'passed':passed,'matches_run':0,'scope':'Two-turn integration, candidate Queen and donor on same team, other dragons fixed; intentional fixture stop at round2.',
            'source':freeze,'map_sha256':digest(raw),'replay_sha256':digest(replay),'frames':frames,'observed':observed,'notices':notices,
            'donor_death_reason':death['reason'],'queen_start':3,'queen_after':next(x['length'] for x in observed if (x['round'],x['id'])==(2,0))}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'passed':passed,'queen_after':result['queen_after'],'outputs':[f['output'] for f in frames]}))
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
