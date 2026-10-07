"""Check the response witness physics with fixed replies in the official engine."""
import hashlib,json,re
from pathlib import Path
from unswbc.engine import EngineModule,DEBUG_ALL,DEBUG_LIMITS

def main():
    out=Path('test-results/reply-physics-contract');out.mkdir(exist_ok=True);rows=[]
    for length,food,expected in ((3,False,True),(2,False,False),(2,True,True)):
        name=f'length{length}-food{int(food)}';tile='TILE_COUNT 1\nTILE 6 5 1 1\n' if food else 'TILE_COUNT 0\n'
        body='7 5 7 6 6 6' if length==3 else '7 5 7 6'
        raw=(f'MAP 20 20\nMAP_NAME Reply physics\n{tile}EDGE_COUNT 0\nDRAGON_COUNT 2\nDRAGON 0 3 4 5 3 5 2 5\nDRAGON 1 {length} {body}\n').encode()
        deaths=[];notices=[];frames=[]
        def reply(i,block):
            rnd=int(re.search(rb'^ROUND (\d+)',block,re.M)[1])
            answer=b'ENDTURN\n' if rnd else (b'MOVE E\nPROTOCOL 3\nENDTURN\n' if i==0 else b'MOVE WW\nPROTOCOL 3\nENDTURN\n')
            frames.append({'round':rnd,'id':i,'output':answer.decode()});return answer
        engine=EngineModule();engine.run(raw,reply,on_death=lambda i,r,reason:deaths.append({'id':i,'round':r,'reason':reason}),
                                       on_notice=notices.append,debug=DEBUG_ALL|DEBUG_LIMITS,seed=2026100786)
        replay=engine.replay('fixed-queen','fixed-reply');(out/f'{name}.replay').write_bytes(replay)
        hit=any(d['id']==0 and d['round']==0 and d['reason']=='H' for d in deaths)
        rows.append({'case':name,'expected_queen_hit':expected,'queen_hit':hit,'passed':hit==expected and not notices,
                     'deaths':deaths,'notices':notices,'frames':frames,'map':raw.decode(),'replay_sha256':hashlib.sha256(replay).hexdigest()})
    result={'passed':all(r['passed'] for r in rows),'matches_run':0,'scope':'One-turn fixed-reply physics, intentional stop at round1. No strength games or bot-vs-bot comparison.','cases':rows}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
