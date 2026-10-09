"""Audit measured own actions in already identity-verified public series."""
import json
from pathlib import Path
from audit_online import load_replay

ROOT = Path(__file__).resolve().parents[1] / 'test-results/oct8-sprint'
rows = []
for directory in sorted(ROOT.glob('v3[01]-*')):
    analysis = directory / 'analysis.json'
    if not analysis.exists():
        continue
    data = json.loads(analysis.read_text(encoding='utf8'))
    own = data['summary']['own_team']
    for match in data['matches']:
        path = directory / 'raw' / f"M{match['match_id']}.replay"
        replay = load_replay(path, node_path='D:/node/node.exe')
        teams = {d['id']: d['team'] for d in replay['initial_dragons']}
        measurements = []
        for event in replay['events']:
            if event['type'] == 'dragonSplit':
                teams[event['childId']] = event['team']
            if event['type'] == 'dragonAction' and teams[event['id']] == own:
                if 'instructions' in event:
                    measurements.append(event['instructions'])
        rows.append({'match_id': match['match_id'], 'version': data['summary']['version'],
                     'source': str(path.relative_to(ROOT)), 'own_team': own,
                     'own_actions_measured': len(measurements),
                     'peak': max((m['count'] for m in measurements), default=0),
                     'exceeded': sum(bool(m['exceeded']) for m in measurements)})
assert len({r['match_id'] for r in rows}) == len(rows)
summary = {str(v): {'games': sum(r['version'] == v for r in rows),
                   'actions': sum(r['own_actions_measured'] for r in rows if r['version'] == v),
                   'peak': max(r['peak'] for r in rows if r['version'] == v),
                   'exceeded': sum(r['exceeded'] for r in rows if r['version'] == v)}
           for v in (30, 31)}
(ROOT / 'v30-v31-runtime-audit.json').write_text(json.dumps({'summary': summary, 'matches': rows}, indent=2), encoding='utf8')
print(json.dumps(summary))
