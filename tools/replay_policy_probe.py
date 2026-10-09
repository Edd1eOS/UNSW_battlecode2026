"""Check a policy on verified historic queen observations until first divergence."""
import argparse,gzip,json,re
from pathlib import Path
from verify_candidate import build
from unswbc.sandbox import SandboxBot,WasmPool

class AuditedBot(SandboxBot):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.restarts=[]
    def _fresh(self):
        if self._box is not None:
            self.restarts.append({"round":getattr(self,"active_round",None),"reason":self._reason(),"points":self.live[0],"memory":self.live[1]})
        super()._fresh()

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--observations',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--team',default='A')
    a=p.parse_args();wasm,digest=build(a.candidate);pool=WasmPool([str(wasm)],key='historic-queen-probe');rows=[]
    try:
        for path in sorted(a.observations.glob('*-observations.json.gz')):
            d=json.loads(gzip.decompress(path.read_bytes()))
            assert d['physical_events_equal']
            for who,q in d['queens'].items():
                if f'TEAM {a.team}\n' not in q['init']:continue
                bot=AuditedBot(pool,init=q['init'].encode(),name=who);turns=[]
                try:
                    for f in q['frames']:
                        bot.active_round=f['round']
                        output=bot.ask(f['input'].encode()).decode();actions=re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$',output,re.M)
                        matches=actions==[f['action']]
                        turns.append({'round':f['round'],'expected':f['action'],'output':output,'matches':matches,'points':bot.live[0],'error':bot.error})
                        if not matches or bot.error:break
                finally:bot.stop()
                row={'source':d['source'],'source_sha256':d['source_sha256'],'queen':int(who),'total_frames':len(q['frames']),'checked':len(turns),'all_equal':len(turns)==len(q['frames']) and all(t['matches'] for t in turns),'turns':turns,'restarts':bot.restarts}
                rows.append(row);print(path.stem,'equal',row['all_equal'],'checked',len(turns),'of',len(q['frames']),flush=True)
    finally:pool.close()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(gzip.compress(json.dumps({'candidate':str(a.candidate),'source_hash':digest,'rows':rows}).encode()))

if __name__=='__main__':main()
