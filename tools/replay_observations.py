"""Re-enact recorded actions in the official engine to recover legal observations.

This is an audit, not a new strength game. Opponents execute only recorded
actions. Sonar is omitted (the v66 decision code does not read it). Reconstructed
physical events must exactly equal the original before observations are trusted.
"""
import argparse, gzip, json, re
from pathlib import Path
from dataclasses import asdict
from audit_online import load_replay
from unswbc.engine import EngineModule

PHYSICAL = {'roundStart','turnStart','dragonAction','dragonUpdate','dragonSplit',
            'dragonDeath','tileChange','pearlCountdown'}

def recover(path, out, ids=(0,1), probe_forward_sonar=False):
    data=load_replay(path,node_path='D:/node/node.exe')
    actions=[]; rnd=None
    for e in data['events']:
        if e['type']=='roundStart': rnd=e['round']
        elif e['type']=='dragonAction': actions.append((rnd,e['id'],e['action']))
    index=0; frames={}; inits={}; notices=[]; divergence=[]
    def spawn(i,block): inits[i]=block.decode()
    def reply(i,block):
        nonlocal index
        r=int(re.search(rb'^ROUND (\d+)',block,re.M)[1])
        if divergence: return b'ENDTURN\n'
        er,ei,action=actions[index]; index+=1
        if (er,ei)!=(r,i):
            divergence.append(f'Action sequence diverged: {(er,ei)} != {(r,i)}')
            return b'ENDTURN\n'
        if action is None: raise ValueError('Unknown action cannot be replayed')
        kind=action['kind']
        cmd=('MOVE '+''.join(action['steps']) if kind=='move' else
             'SPLIT '+str(action['childSegmentCount']) if kind=='split' else '')
        if kind not in ('move','split','suicide'): raise ValueError(kind)
        if i in ids: frames.setdefault(i,[]).append({'round':r,'input':block.decode(),'action':cmd})
        ping=''
        if probe_forward_sonar and i in (0,1):
            direction=action['steps'][-1] if kind=='move' and action['steps'] else re.search(rb'^DIR ([NESW])',block,re.M)[1].decode()
            ping='SONAR '+direction+' 0\n'
        return (cmd+'\n'+ping+'PROTOCOL 3\nENDTURN\n').encode()
    # Public replay maps redact pearl timers to zero. Restore timers only from
    # a same-name official map, then prove the whole physical event stream.
    map_name=next(x for x in data['map'].splitlines() if x.startswith('MAP_NAME '))
    matches=[p for p in Path('maps/current').glob('*.map') if map_name in p.read_text().splitlines()]
    map_text=data['map']; restored=None
    if len(matches)==1:
        tile_lines={tuple(x.split()[1:3]):x for x in matches[0].read_text().splitlines() if x.startswith('TILE ')}
        map_text='\n'.join(tile_lines.get(tuple(x.split()[1:3]),x) if x.startswith('TILE ') else x for x in map_text.splitlines())+'\n'
        restored=str(matches[0])
    engine=EngineModule()
    result=engine.run(map_text.encode(),reply,bot_spawn=spawn,on_notice=notices.append,seed=int(data['seed']))
    rebuilt=out/(path.stem+'-reconstructed.replay');rebuilt.write_bytes(engine.replay('recorded-A','recorded-B'))
    actual=load_replay(rebuilt,node_path='D:/node/node.exe')
    a=[{k:v for k,v in e.items() if k!='instructions'} for e in data['events'] if e['type'] in PHYSICAL-{'pearlCountdown'}]
    b=[{k:v for k,v in e.items() if k!='instructions'} for e in actual['events'] if e['type'] in PHYSICAL-{'pearlCountdown'}]
    if a!=b:
        first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
        raise ValueError(f'Physics diverged at {first}: {a[first:first+1]} != {b[first:first+1]}')
    evidence={'source':str(path),'source_sha256':data['input_sha256'],'physical_events_equal':True,
              'physical_events':len(a),'actions':index,'result':asdict(result),'notices':notices,'restored_map':restored,
              'scope':('Recorded physical actions with one forward Queen sonar injected; only conditional sensing evidence, no counterfactual wins or opponent response modelling.' if probe_forward_sonar else 'Recorded-action reconstruction; no counterfactual wins. Sonar omitted; only for policies that ignore inbox/echo.'),
              'queens':{str(i):{'init':inits[i],'frames':v} for i,v in frames.items()}}
    (out/(path.stem+'-observations.json.gz')).write_bytes(gzip.compress(json.dumps(evidence).encode()))
    print(path.stem,'verified',len(a),'events',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--replays',nargs='+',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--ids',nargs='+',type=int,default=[0,1])
    p.add_argument('--probe-forward-sonar',action='store_true')
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    failures=[]
    for source in args.replays:
        try: recover(source,args.out,args.ids,args.probe_forward_sonar)
        except Exception as error:
            failures.append({'source':str(source),'error':str(error)})
            print(source.stem,'UNVERIFIED',str(error)[:200],flush=True)
    (args.out/'last-run-failures.json').write_text(json.dumps(failures,indent=2))
    if failures: raise SystemExit(1)
