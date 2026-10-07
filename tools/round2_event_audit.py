"""Read-only, hash-bound gameplay equivalence and first divergent action audit.

No bot/match execution. Ignore only logs and indicator strings in gameplay
equivalence; preserve actions, state updates, resource events, ordering and result.
Equal-prefix first action is useful for diagnosis, not an outcome causal estimate.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import audit_online


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(result_path, expected):
    path = Path(result_path)
    raw = path.read_bytes()
    assert sha(raw) == expected['result_json_sha256']
    row = json.loads(raw)
    replay = Path(row['replay']['path'])
    if not replay.is_absolute():
        replay = path.parent / replay
    assert sha(replay.read_bytes()) == row['replay']['sha256'] == expected['replay_sha256']
    data = audit_online.load_replay(replay)
    assert data['decoder_bundle_sha256'] == expected['decoder_bundle_sha256']
    return row, data


def events(data):
    return [e for e in data['events'] if e['type'] not in ('dragonIndicator', 'dragonLog')]


def turns(data):
    rd = -1
    notes = {}
    actions = []
    for event in data['events']:
        if event['type'] == 'roundStart':
            rd = event['round']
        elif event['type'] == 'turnStart':
            notes[event['id']] = ''
        elif event['type'] == 'dragonIndicator':
            notes[event['id']] = event['text']
        elif event['type'] == 'dragonAction':
            actions.append({'round': rd, 'id': event['id'], 'action': event['action'],
                            'indicator': notes.get(event['id'], '')})
    return actions


def build(comparison):
    report = json.loads(comparison.read_bytes())
    rows = []
    for pair in report['pairs']:
        if pair['issues']:
            rows.append({'key': pair['key'], 'issues': pair['issues']})
            continue
        br, b = read(pair['baseline_result'], pair['baseline_provenance'])
        cr, c = read(pair['candidate_result'], pair['candidate_provenance'])
        be, ce = events(b), events(c)
        bt, ct = turns(b), turns(c)
        first = None
        for index, (x, y) in enumerate(zip(bt, ct)):
            if any(x[k] != y[k] for k in ('round', 'id', 'action')):
                first = {'action_index': index, 'baseline': x, 'candidate': y}
                break
        if first is None and len(bt) != len(ct):
            first = {'action_index': min(len(bt), len(ct)), 'different_action_count': [len(bt), len(ct)]}
        candidate_ids = {d['id'] for d in c['initial_dragons'] if d['team'] == cr['candidate_team']}
        for e in c['events']:
            if e['type'] == 'dragonSplit' and e['team'] == cr['candidate_team']:
                candidate_ids.add(e['childId'])
        counts = Counter()
        for t in ct:
            if t['id'] not in candidate_ids:
                continue
            f = dict(s.split('=', 1) for s in t['indicator'].split() if '=' in s)
            if f.get('role') in ('Q', 'RESERVE', 'LAST'):
                counts['protected_actions'] += 1
                if f.get('terrain_tier') == '0':
                    counts['protected_finite_selected'] += 1
                if f.get('terrain_tier') == '1' and f.get('outside') == '0' and int(f.get('depth', 8)) < 6:
                    counts['terrain_preferred_but_short_visible_continuation'] += 1
            if int(f.get('resource_marked', 0)) > 0:
                counts['resource_marked_actions'] += 1
            if int(f.get('resource_cost', 0)) > 0:
                counts['resource_discounted_selected_actions'] += 1
        rows.append({'key': pair['key'], 'eligible_pair': pair['eligible_pair'],
                     'baseline_provenance': pair['baseline_provenance'],
                     'candidate_provenance': pair['candidate_provenance'],
                     'gameplay_events_equal': be == ce,
                     'gameplay_sha256': [sha(canonical(be)), sha(canonical(ce))],
                     'initial_state_equal': b['map'] == c['map'] and b['seed'] == c['seed'] and b['initial_dragons'] == c['initial_dragons'],
                     'formal_result_equal': pair['baseline_formal_result'] == pair['candidate_formal_result'],
                     'first_divergent_action': first, 'candidate_diagnostics': dict(counts)})
    return {'scope': __doc__, 'comparison_sha256': sha(comparison.read_bytes()),
            'driver_sha256': sha(Path(__file__).read_bytes()),
            'decoder_loader_sha256': sha(Path(audit_online.__file__).read_bytes()),
            'matches_run': 0, 'pairs': rows,
            'summary': {'pairs': len(rows), 'issues': sum(bool(r.get('issues')) for r in rows),
                        'equal_gameplay': sum(r.get('gameplay_events_equal', False) for r in rows),
                        'equal_formal_result': sum(r.get('formal_result_equal', False) for r in rows)},
            'limits': ['Diagnostics describe selected actions, not rejected alternatives or global safety.',
                       'First action difference identifies a changed decision before action paths diverge; it does not identify the cause of the final score.',
                       'Equal gameplay is restricted to these completed external fixtures; CPU/diagnostic output may differ.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.comparison)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['summary']))
