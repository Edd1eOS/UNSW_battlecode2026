"""Explain two exposed resource-V2 outcomes with exact Queen capital ledgers.

Post-outcome diagnostic cases; no new matches and no general strength inference.
"""
import hashlib
import json
from pathlib import Path
import round2_event_audit as audit
import trajectory_metrics
import oct7_reconstruct_portals as observation

ROOT = Path(__file__).resolve().parents[1]


def neighborhoods(replay, queen, selected_rounds):
    """Omniscient replay diagnosis only; never supplied as bot observations."""
    board = observation.Board(replay['map'])
    live = {d['id']: {'team': d['team'], 'body': list(map(observation.point, d['body']))}
            for d in replay['initial_dragons']}
    rd = None
    rows = []
    for e in replay['events']:
        kind = e['type']
        if kind == 'roundStart':
            rd = e['round']
        elif rd is None:
            continue
        elif kind == 'turnStart' and e['id'] == queen and rd in selected_rounds:
            head = live[queen]['body'][0]
            neighbors = []
            for direction in observation.DIRS:
                target = board.step(head, direction)
                occupants = [{'id': identity, 'team': d['team'], 'body_index': index,
                              'length': len(d['body']), 'same_team': d['team'] == live[queen]['team']}
                             for identity, d in live.items() for index, p in enumerate(d['body']) if p == target]
                neighbors.append({'direction': direction, 'target': target, 'occupants': occupants})
            rows.append({'round': rd, 'head': head, 'length': len(live[queen]['body']), 'neighbors': neighbors})
        elif kind == 'dragonUpdate':
            body = [observation.point(e['head']), *live[e['id']]['body']]
            tail = observation.point(e['tail'])
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            assert body[-1] == tail
            live[e['id']]['body'] = body
        elif kind == 'dragonSplit':
            live[e['parentId']]['body'] = list(map(observation.point, e['parentBody']))
            live[e['childId']] = {'team': e['team'], 'body': list(map(observation.point, e['childBody']))}
        elif kind == 'dragonDeath':
            del live[e['id']]
    return rows, trajectory_metrics.scores(live)


def main():
    comparison = ROOT / 'test-results/round2-resource-v2-kgts-compare.json'
    events = ROOT / 'test-results/round2-resource-v2-kgts-event-audit.json'
    report = json.loads(comparison.read_text(encoding='utf-8'))
    actions = json.loads(events.read_text(encoding='utf-8'))
    assert actions['comparison_sha256'] == audit.sha(comparison.read_bytes())
    by_key = {tuple(r['key']): r for r in actions['pairs']}
    rows = []
    for pair in report['pairs']:
        if (pair['key'][2], pair['key'][-1]) not in (('australia', 'B'), ('big_empty', 'A')):
            continue
        assert pair['gross_eligible_pair'] and not pair['issues']
        row = {'key': pair['key'], 'first_divergent_action': by_key[tuple(pair['key'])]['first_divergent_action']}
        for arm in ('baseline', 'candidate'):
            record, replay = audit.read(pair[arm + '_result'], pair[arm + '_provenance'])
            team = record['candidate_team']
            core = trajectory_metrics.analyze_replay(replay)
            initial = core['initial']['scores'][team]['queen_length']
            m = pair['whole_match'][arm]['metrics']
            residual = initial + m['queen_food_collected'] - m['queen_paid_step_cost'] - m['queen_split_transfer'] - m['queen_death_length'] - m['queen_length']
            assert residual == 0
            deaths = [d for d in core['deaths'] if d['team'] == team and d['is_queen']]
            queen_ids = {d['id'] for d in replay['initial_dragons'] if d['team'] == team and d['id'] <= 1}
            queen_actions = [a for a in audit.turns(replay) if a['id'] in queen_ids]
            adjacent, final_scores = neighborhoods(replay, next(iter(queen_ids)),
                                                   {r for d in deaths for r in range(max(0, d['round'] - 5), d['round'] + 1)})
            assert final_scores[team]['queen_length'] == m['queen_length']
            assert final_scores[team]['total_length'] == m['total_length']
            row[arm] = {'provenance': pair[arm + '_provenance'], 'queen_initial_length': initial,
                        'queen_final_length': m['queen_length'], 'food': m['queen_food_collected'],
                        'paid': m['queen_paid_step_cost'], 'split_transfer': m['queen_split_transfer'],
                        'death_length': m['queen_death_length'], 'balance_residual': residual,
                        'queen_deaths': deaths,
                        'omniscient_replay_neighborhoods_not_bot_input': adjacent,
                        'last_queen_actions_at_each_death': [
                            [a for a in queen_actions if a['round'] <= d['round']][-3:] for d in deaths],
                        'whole_metrics': m}
        rows.append(row)
    out = ROOT / 'docs/oct7-round2-case-ledgers.json'
    out.write_text(json.dumps({'scope': __doc__, 'matches_run': 0,
                               'comparison_sha256': audit.sha(comparison.read_bytes()),
                               'action_audit_sha256': audit.sha(events.read_bytes()),
                               'driver_sha256': audit.sha(Path(__file__).read_bytes()),
                               'trajectory_analyzer_sha256': audit.sha(Path(trajectory_metrics.__file__).read_bytes()),
                               'board_decoder_sha256': audit.sha(Path(observation.__file__).read_bytes()),
                               'cases': rows,
                               'limits': ['Rounds are zero based.', 'A first different action and later death do not isolate the causal mechanism across diverged games.',
                                          'Queen final growth may come from retaining split capital; food collection is reported independently.']},
                              ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cases': len(rows), 'file': str(out),
                      'queen_deaths': [r['candidate']['queen_deaths'] for r in rows]}))


if __name__ == '__main__':
    main()
