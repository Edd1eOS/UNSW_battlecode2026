"""Compare actual physical prefixes of the budget-stopped original panel."""
import json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from audit_online import load_replay
from replay_observations import PHYSICAL
root=Path('test-results');old=root/'oct7-night-v66-panel';new=root/'oct7-night-v114-audited'
def one(path):
    relative=path.relative_to(old);a=json.loads(path.read_text());b=json.loads((new/relative).read_text())
    assert (a['seed'],a['map_sha256'],a['candidate_team'])==(b['seed'],b['map_sha256'],b['candidate_team'])
    x=load_replay(Path(a['replay']['path']),node_path='D:/node/node.exe');y=load_replay(Path(b['replay']['path']),node_path='D:/node/node.exe')
    def events(d):return [{k:v for k,v in e.items() if k!='instructions'} for e in d['events'] if e['type'] in PHYSICAL-{'pearlCountdown'}]
    u,v=events(x),events(y);i=next((i for i,(f,g) in enumerate(zip(u,v)) if f!=g),min(len(u),len(v)));r=next((e['round'] for e in reversed(u[:i+1]) if e['type']=='roundStart'),None)
    return {'map':a['map'],'team':a['candidate_team'],'seed':a['seed'],'old_replay_sha256':a['replay']['sha256'],'new_replay_sha256':b['replay']['sha256'],'physical_equal':u==v,'common_physical_events':i,'first_different_round':r if u!=v else None,'old_event':u[i:i+1],'new_event':v[i:i+1]}
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,sorted(old.glob('games/**/result.json'))))
out={'scope':'Only nine completed original discovery games; identical seed/map/side/external bot. Instruction counts are excluded. No claim of full-panel equivalence.','games':rows}
(root/'oct7-night-cache-equivalence.json').write_text(json.dumps(out,indent=2))
print(json.dumps(rows))
