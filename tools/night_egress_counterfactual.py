"""One-turn engine intervention. Never a strength game or counterfactual win."""
import json,re
from pathlib import Path
from audit_online import load_replay
from verify_candidate import build
from replay_policy_probe import AuditedBot
from unswbc.sandbox import WasmPool
from unswbc.engine import EngineModule

out=Path('test-results/oct7-night-egress-contract');out.mkdir(exist_ok=True)
source=Path('test-results/colony-online-baseline/raw/M1344086.replay')
d=load_replay(source,node_path='D:/node/node.exe');acts={};children={};r=None
for e in d['events']:
    if e['type']=='roundStart':r=e['round']
    if e['type']=='dragonSplit':children[r,e['parentId']]=e['childId']
    if e['type']=='dragonAction':
        a=e['action'];acts[r,e['id']]=('MOVE '+''.join(a['steps']) if a['kind']=='move' else 'SPLIT '+str(a['childSegmentCount']) if a['kind']=='split' else '')
name=next(x for x in d['map'].splitlines() if x.startswith('MAP_NAME '))
mapfile=next(p for p in Path('maps/current').glob('*.map') if name in p.read_text().splitlines())
tiles={tuple(x.split()[1:3]):x for x in mapfile.read_text().splitlines() if x.startswith('TILE ')}
maptext='\n'.join(tiles.get(tuple(x.split()[1:3]),x) if x.startswith('TILE ') else x for x in d['map'].splitlines())+'\n'
wasm,digest=build(Path('opponents/v111-queen-egress-wait'));pool=WasmPool([str(wasm)],key='egress-contract');bots={};branch=False;observed=[];queen121=False;identity_map={};current=None

def spawn(i,b):
    original = i if not branch else children.get((current[0],identity_map.get(current[1])))
    identity_map[i]=original
    if i in (0,166) or (original is None and b'TEAM A\n' in b):bots[i]=AuditedBot(pool,init=b,name=str(i))
def reply(i,b):
    global branch,queen121,current
    r=int(re.search(rb'^ROUND (\d+)',b,re.M)[1]);current=(r,i)
    if r>=121:
        if i==0 and r==121:queen121=True
        return b'ENDTURN\n'
    original_id=identity_map[i]
    recorded=acts.get((r,original_id),'')
    use=(i==166 and r>=119) or (i==0 and r>=120) or (original_id is None)
    if i in bots:
        response=bots[i].ask(b).decode();actions=re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$',response,re.M)
        assert len(actions)==1 and not bots[i].error,(i,r,response,bots[i].error)
        if not use:assert actions==[recorded],(i,r,actions,recorded)
        else:
            recorded=actions[0];observed.append({'id':i,'round':r,'action':recorded,'input':b.decode(),'output':response})
    if i==166 and r==119:branch=True
    return (recorded+'\nPROTOCOL 3\nENDTURN\n').encode()
engine=EngineModule()
try:
    engine.run(maptext.encode(),reply,bot_spawn=spawn,seed=int(d['seed']))
    replay=out/'intervention.replay';replay.write_bytes(engine.replay('one-turn-intervention','recorded-opponent'))
    rebuilt=load_replay(replay,node_path='D:/node/node.exe')
finally:
    for bot in bots.values():bot.stop()
    pool.close()
physical={'roundStart','turnStart','dragonAction','dragonUpdate','dragonSplit','dragonDeath','tileChange'}
def prefix(events):
    result=[];r=None
    for e in events:
        if e['type']=='roundStart':r=e['round']
        if r==119 and e['type']=='dragonAction' and e['id']==166:break
        if e['type'] in physical:result.append({k:v for k,v in e.items() if k!='instructions'})
    return result
assert prefix(d['events'])==prefix(rebuilt['events'])
assert observed[0]['action']=='SPLIT 2'
report={'source':str(source),'source_sha256':d['input_sha256'],'candidate_sha256':digest,'prefix_exact':True,'queen_alive_at_round121':queen121,'intervention':observed,'scope':'Only immediate survival to round121 is tested. Other existing dragons follow recorded actions through120; all terminate at121. No counterfactual winner is inferred.'}
(out/'result.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='intervention'}));print([(x['id'],x['round'],x['action']) for x in observed])
