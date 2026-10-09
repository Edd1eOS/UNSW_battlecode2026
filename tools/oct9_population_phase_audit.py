"""Read-only population and Queen-death audit of finished local engine panels."""
from pathlib import Path
from collections import Counter
import argparse
import json
from tools.audit_online import load_replay


def one(path):
    meta = json.loads((path / 'result.json').read_text())
    replay = load_replay(path / 'raw.replay', node_path='D:/node/node.exe')
    team = meta['candidate_team']
    live = {d['id']: {'team': d['team'], 'body': [(p['x'], p['y']) for p in d['body']]}
            for d in replay['initial_dragons']}
    queens = {t: next(i for i, d in live.items() if i <= 1 and d['team'] == t) for t in 'AB'}
    rnd = -1
    actor = None
    notes = {}
    counts = {t: {'early': Counter(), 'late': Counter()} for t in 'AB'}
    snapshots = {}
    deaths = []

    def snapshot():
        return {t: {'units': sum(d['team'] == t for d in live.values()),
                    'queen': len(live.get(queens[t], {}).get('body', [])),
                    'longest': max([len(d['body']) for d in live.values() if d['team'] == t] or [0]),
                    'total': sum(len(d['body']) for d in live.values() if d['team'] == t)} for t in 'AB'}

    for index, event in enumerate(replay['events']):
        kind = event['type']
        if kind == 'roundStart':
            if rnd in (49, 99, 149, 199, 249, 299, 349, 399, 449, 499):
                snapshots[str(rnd)] = snapshot()
            rnd = event['round']
        elif kind == 'turnStart':
            actor = event['id']
        elif kind == 'dragonIndicator':
            notes[event['id']] = event['text']
        elif kind == 'dragonUpdate' and rnd >= 0:
            body = [(event['head']['x'], event['head']['y'])] + live[event['id']]['body']
            tail = event['tail']['x'], event['tail']['y']
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            assert body[-1] == tail
            live[event['id']]['body'] = body
        elif kind == 'dragonSplit':
            phase = 'early' if rnd < 150 else 'late'
            count = counts[event['team']][phase]
            count['splits'] += 1
            note = notes.get(event['parentId'], '')
            count['ordinary_splits' if ' FLOOD ' in note else 'emergency_splits'] += 1
            if event['parentId'] <= 1:
                count['queen_splits'] += 1
            for ident, key in ((event['parentId'], 'parentBody'), (event['childId'], 'childBody')):
                live[ident] = {'team': event['team'], 'body': [(p['x'], p['y']) for p in event[key]]}
        elif kind == 'dragonDeath':
            ident = event['id']
            dying = live[ident]
            counts[dying['team']]['early' if rnd < 150 else 'late']['death_' + event['reason']] += 1
            if ident <= 1:
                deaths.append({'queen_id': ident, 'team': dying['team'], 'round': rnd,
                               'reason': event['reason'], 'length': len(dying['body']),
                               'body_before_death': dying['body'], 'actor': actor,
                               'actor_team': live.get(actor, {}).get('team'),
                               'last_queen_note': notes.get(ident), 'last_actor_note': notes.get(actor),
                               'nearby_events': replay['events'][max(0, index - 5):index + 3]})
            del live[ident]
    snapshots['final'] = snapshot()
    return {'game': path.name, 'candidate_team': team, 'result': meta['official_outcome'],
            'engine_result': meta['engine_result'], 'peak': meta['peak'][team]['points'],
            'invalid': meta['invalid_runtime_events'], 'phase_counts': counts,
            'snapshots_round_index': snapshots, 'queen_deaths': deaths}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('panel')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    rows = [one(p.parent) for p in sorted((Path(args.panel) / 'games').glob('*/result.json'))]
    output = {'scope': 'Read-only completed engine replay audit. Round phase cutoff is zero-based round 150. No causal attribution between changed versions.',
              'games': rows}
    Path(args.out).write_text(json.dumps(output, indent=2), encoding='utf-8')
    for row in rows:
        t = row['candidate_team']
        print(json.dumps({'game': row['game'], 'result': row['result'], 'peak': row['peak'],
                          'invalid': row['invalid'], 'snapshots': {k: v[t] for k, v in row['snapshots_round_index'].items()},
                          'late': row['phase_counts'][t]['late'],
                          'queen_deaths': [{k: v for k, v in d.items() if k != 'nearby_events'}
                                           for d in row['queen_deaths'] if d['team'] == t]}))
