"""Bind Oct 7 evening sources, frozen experiments and online results to files."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'test-results'

def identity(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def source(path):
    files = {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob('*')
             if p.is_file() and p.suffix in ('.cpp', '.hpp', '.h', '.toml')}
    return {'path': path.relative_to(ROOT).as_posix(),
            'protocol_source_sha256': hashlib.sha256(b''.join(k.encode()+v for k,v in sorted(files.items()))).hexdigest(),
            'files': [identity(path / name) for name in sorted(files)]}

def main():
    panels=[]
    for folder in sorted(RESULTS.glob('oct7-night-*')):
        if not (folder/'plan.json').exists(): continue
        results=[]
        for path in sorted((folder/'games').rglob('result.json')):
            d=json.loads(path.read_text(encoding='utf8'))
            results.append({**identity(path), 'id':d['id'], 'outcome':d.get('official_outcome'),
                'eligible':d.get('eligible_mechanism_result'), 'peak':d.get('peak',{}).get(d['candidate_team']),
                'runtime_errors':d.get('runtime_errors'), 'budget_passed':d.get('candidate_budget_margin_passed'),
                'failure':d.get('error',d.get('infrastructure_error'))})
        panels.append({'path':folder.relative_to(ROOT).as_posix(), 'plan':identity(folder/'plan.json'),
            'summary':json.loads((folder/'summary.json').read_text()) if (folder/'summary.json').exists() else None,
            'results':results})
    online=[]
    for name in ('oct7-night-okbro-v14','oct7-night-okbro-v22','oct7-night-okbro-v23',
                 'oct7-night-goated-v23-first9','oct7-night-goated-v23-last8','oct7-night-recent','colony-online-baseline'):
        folder=RESULTS/name;d=json.loads((folder/'analysis.json').read_text(encoding='utf8'))
        online.append({'analysis':identity(folder/'analysis.json'), 'summary':d['summary'],
            'role':'new_unranked_probe' if name not in ('oct7-night-recent','colony-online-baseline') else 'previous_research_material',
            'matches':[{k:r[k] for k in ('match_id','metadata','raw_sha256','public_header_teams','final','quality','gross_verified','ui_winner_consistent')} for r in d['matches']]})
    combined=[r for o in online if 'goated-v23-' in o['analysis']['path'] for r in o['matches']]
    maps=[r['metadata']['text'].split('· ')[1].split('\n')[0] for r in combined]
    assert len(combined)==17 and len(set(maps))==17
    assert sum(r['final']['leader']=='A' for r in combined)==2
    artifacts=[]
    for path in sorted(RESULTS.glob('oct7-night-*')):
        if path.is_file(): artifacts.append(identity(path))
        elif 'contract' in path.name:
            artifacts.extend(identity(p) for p in sorted(path.glob('result.json')))
    sources=[source(p) for p in sorted((ROOT/'opponents').glob('v11[0-9]-*'))]
    sources.insert(0,source(ROOT/'opponents/v66-queen-threat-buffer'))
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Two-hour autonomous research. Same-seed reruns are not independent samples. Online probes cannot freeze random seeds or private opponent submission IDs.',
        'active':{'version':14,'submission_id':15719,'source':'opponents/v66-queen-threat-buffer',
                  'reason':'No new candidate met preregistered high-rank adoption evidence; 1800 target not reached.'},
        'uploads':[{'version':22,'submission_id':19649,'source':'opponents/v114-evaluation-cache'},
                   {'version':23,'submission_id':19663,'source':'opponents/v118-newborn-threat'}],
        'holdout':{'seed':2026100749,'opened_for':'v118 only','not_independent_for_later_candidates':True},
        'sources':sources,'panels':panels,'online':online,'artifacts':artifacts,
        'tools':[identity(p) for p in sorted((ROOT/'tools').glob('night_*.py'))]+[identity(ROOT/'tools'/p) for p in ('replay_observations.py','replay_policy_probe.py')],
        'checks':[identity(p) for p in sorted((ROOT/'tests').glob('v11*_test.cpp'))]}
    out=ROOT/'docs/oct7-night-evidence.json'
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'manifest':str(out),'sources':len(sources),'panels':len(panels),'online_groups':len(online),'new_online_games':68}))

if __name__=='__main__':main()
