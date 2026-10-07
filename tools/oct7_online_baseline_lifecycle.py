"""Offline lifecycle supplement for a complete, explicitly selected online audit.

Reads immutable audit caches and raw replays. No matches or bot execution.
Whole-game lead and fixed 0-99 / 100-299 / 300-end phases cover every round.
Raw world state is used only for post-match collision attribution, never as input
to a bot or as a reconstruction of its private memory or intentions.
"""
from __future__ import annotations
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

try:
    from . import audit_online
except ImportError:
    import audit_online


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(p):
    return (p['x'], p['y']) if isinstance(p, dict) else tuple(p)


def describe(values):
    return {'n': len(values), 'sum': sum(values),
            'median': statistics.median(values) if values else None,
            'mean': statistics.mean(values) if values else None}


def friendly_collision(path, cached):
    data = audit_online.load_replay(path)
    own = cached['metrics']['our_team']
    queen = next(d for d in cached['queens'] if d['team'] == own)
    qid = queen['id']
    target = next(d for d in cached['deaths'] if d['team'] == own and d['is_queen'])
    pair = next(p for p in cached['audit']['head_collision_pairs']
                if qid in p['ids'] and p['round'] == target['round'] + 1)
    assert pair['kind'] == 'friendly'
    partner = next(i for i in pair['ids'] if i != qid)
    size = re.search(r'^MAP\s+(\d+)\s+(\d+)', data['map'], re.M)
    width, height = map(int, size.groups())

    def visible(p, center):
        dx, dy = abs(p[0] - center[0]), abs(p[1] - center[1])
        return min(dx, width - dx) <= 3 and min(dy, height - dy) <= 3

    live = {d['id']: {'team': d['team'], 'body': list(map(point, d['body']))}
            for d in data['initial_dragons']}
    round0, actor, turn, last_queen = -1, None, None, None
    births = {}
    for event_index, event in enumerate(data['events']):
        kind = event['type']
        if kind == 'roundStart':
            round0 = event['round']
        elif kind == 'turnStart':
            actor = event['id']
            turn = {'round0': round0, 'actor': actor, 'event_index': event_index,
                    'snapshot': copy.deepcopy(live), 'action': None, 'indicators': []}
            if actor == qid:
                last_queen = turn
        elif kind == 'dragonAction':
            if turn and event['id'] == actor:
                turn['action'] = copy.deepcopy(event.get('action'))
        elif kind == 'dragonIndicator':
            if turn and event['id'] == actor:
                turn['indicators'].append(copy.deepcopy(event))
        elif kind == 'dragonSplit':
            parent, child = event['parentId'], event['childId']
            live[parent]['body'] = list(map(point, event['parentBody']))
            live[child] = {'team': event['team'], 'body': list(map(point, event['childBody']))}
            births[child] = {'parent_id': parent, 'round0': round0, 'event_index': event_index,
                             'body': copy.deepcopy(live[child]['body'])}
        elif kind == 'dragonUpdate' and round0 >= 0:
            identity = event['id']
            body = [point(event['head'])] + live[identity]['body']
            tail = point(event['tail'])
            while len(body) > 1 and body[-1] != tail:
                body.pop()
            assert body[-1] == tail, (identity, event_index)
            live[identity]['body'] = body
        elif kind == 'dragonDeath':
            if event['id'] == qid:
                assert event_index == target['event_index'] and actor == target['turn_id']
                assert last_queen is not None and turn is not None
                q_before = last_queen['snapshot'][qid]['body'][0]
                partner_before = last_queen['snapshot'].get(partner)
                birth = births.get(partner)
                new_same_round = (birth is not None and birth['round0'] == round0
                                  and partner not in last_queen['snapshot'])
                actor_start = turn['snapshot'][actor]['body'][0]
                queen_at_actor_start = turn['snapshot'][qid]['body'][0]
                return {'match_id': cached['match_id'], 'round0': round0, 'human_round': round0 + 1,
                        'queen_id': qid, 'partner_id': partner, 'moving_actor_id': actor,
                        'queen_moved_into_partner': actor == qid,
                        'partner_origin_at_latest_queen_input': 'newborn_same_round' if new_same_round else 'existing_head',
                        'partner_head_visible_at_latest_queen_input': visible(partner_before['body'][0], q_before)
                            if partner_before else None,
                        'queen_head_visible_at_moving_actor_input': visible(queen_at_actor_start, actor_start),
                        'latest_queen_turn': {k: last_queen[k] for k in ('round0', 'event_index', 'action', 'indicators')},
                        'collision_turn': {k: turn[k] for k in ('round0', 'event_index', 'actor', 'action', 'indicators')},
                        'partner_birth': birth,
                        'actor_start_head': actor_start, 'queen_head_at_actor_input': queen_at_actor_start,
                        'queen_predeath_length': target['last_recorded_length'],
                        'evidence': pair, 'raw_replay_sha256': sha(path),
                        'limits': ['Visibility is the legal toroidal 7x7 turn-start tile window only',
                                   'Historical portal/sonar/private memory is not reconstructed',
                                   'Visible geometric opportunity does not prove a safe alternative or intent']}
            live.pop(event['id'])
    raise ValueError('Expected Queen collision event absent')


def row_record(cached, source_row):
    m = cached['metrics']; own = m['our_team']; other = 'B' if own == 'A' else 'A'
    profiles = {}
    for team in (own, other):
        r, g = cached['resources'][team], cached['gross_resources'][team]
        assert g['food_collected'] - g['paid_step_cost'] == r['recorded_update_net']
        assert r['net_retained_length'] == r['recorded_update_net'] - r['last_recorded_length_removed_on_death']
        profiles[team] = {'food': g['food_collected'], 'paid': g['paid_step_cost'],
                         'net_income': g['food_collected'] - g['paid_step_cost'],
                         'net_retained_body_since_initial': r['net_retained_length'],
                         'final_retained_body': r['final_retained_length'],
                         'body_removed_on_death': r['last_recorded_length_removed_on_death'],
                         'splits': r['splits'], 'initial_capital': r['initial_capital']}
    qown, qother = (cached['final']['scores'][t]['queen_length'] for t in (own, other))
    qstate = ('both_dead' if qown == qother == 0 else 'equal_alive' if qown == qother
              else 'ours_dead_opponent_alive' if qown == 0 else 'both_alive_ours_shorter'
              if qown < qother else 'ours_ahead')
    phases = {}
    for name, begin, end in (('early', 0, 99), ('middle', 100, 299), ('end', 300, 1000000)):
        frames = [f for f in cached['trajectory'] if begin <= f['round'] <= end]
        phases[name] = {'sampled_rounds': len(frames),
                        'our_leading_rounds': sum(f['leader'] == own for f in frames),
                        'opponent_leading_rounds': sum(f['leader'] == other for f in frames),
                        'tied_rounds': sum(f['leader'] is None for f in frames)}
    assert sum(p['sampled_rounds'] for p in phases.values()) == cached['advantage']['sampled_rounds']
    return {'match_id': cached['match_id'], 'map': m['map'], 'opponent': m['opponent'],
            'outcome': m['outcome'], 'score_axis': m['score_axis'], 'our_team': own,
            'clean_no_recorded_invalid_action': not m['opponent_invalid_action_deaths']
                and not m['event_counts'].get('death_invalid_action', 0),
            'terminal_queen_pair': [qown, qother], 'terminal_queen_state': qstate,
            'terminal_longest_pair': [cached['final']['scores'][t]['longest_dragon'] for t in (own, other)],
            'our_historical_event_peak': m['historical_event_longest'],
            'our_peak_minus_opponent_terminal_longest': m['historical_event_longest']
                - cached['final']['scores'][other]['longest_dragon'],
            'our_unique_longest_deaths': len(m['unique_longest_deaths']),
            'our_cumulative_longest_score_drops_on_death': sum(d['longest_length_loss'] for d in m['unique_longest_deaths']),
            'our_unique_longest_deaths_detail': m['unique_longest_deaths'],
            'queen_death': m['queen_death'], 'queen_collision_relation': m['queen_head_collision_relation'],
            'resources': {'ours': profiles[own], 'opponent': profiles[other],
                          'ours_minus_opponent': {k: profiles[own][k] - profiles[other][k] for k in profiles[own]}},
            'sampled_rounds': cached['advantage']['sampled_rounds'],
            'whole_game_lead': cached['advantage']['by_team'][own], 'fixed_phases': phases,
            'source': {'analysis_path': source_row['analysis_path'],
                       'analysis_sha256': sha(Path(source_row['_folder']) / source_row['analysis_path']),
                       'replay_sha256': source_row['replay_sha256']}}


def group(rows):
    def aggregate(items):
        return {'games': len(items), 'outcomes': dict(Counter(r['outcome'] for r in items)),
                'terminal_queen_states': dict(Counter(r['terminal_queen_state'] for r in items)),
                'resources': {side: {k: describe([r['resources'][side][k] for r in items])
                                    for k in ('food', 'paid', 'net_income', 'net_retained_body_since_initial',
                                              'final_retained_body', 'body_removed_on_death', 'splits')}
                              for side in ('ours', 'opponent', 'ours_minus_opponent')},
                'full_game_persistence': {'ever_led_games': sum(r['whole_game_lead']['leading_rounds'] > 0 for r in items),
                    'lost_lead_games': sum(r['whole_game_lead']['lead_losses'] > 0 for r in items),
                    'leading_rounds': describe([r['whole_game_lead']['leading_rounds'] for r in items]),
                    'longest_continuous_lead': describe([r['whole_game_lead']['longest_continuous_lead'] for r in items]),
                    'leading_fraction': describe([r['whole_game_lead']['leading_rounds'] / r['sampled_rounds'] for r in items]),
                    'lead_losses': describe([r['whole_game_lead']['lead_losses'] for r in items])},
                'fixed_phases': {p: {k: sum(r['fixed_phases'][p][k] for r in items)
                                     for k in ('sampled_rounds', 'our_leading_rounds', 'opponent_leading_rounds', 'tied_rounds')}
                                 for p in ('early', 'middle', 'end')}}
    groups = {'all': rows, 'wins': [r for r in rows if r['outcome'] == 'win']}
    for axis in ('elimination', 'queen', 'longest'):
        groups['loss:' + axis] = [r for r in rows if r['outcome'] == 'loss' and r['score_axis'] == axis]
    return {name: aggregate(items) for name, items in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    index_path = args.audit_dir / 'index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    assert index['summary']['full_panel_complete'] and index['summary']['gross_ledger_verified'] == 51
    assert index['summary']['terminal_UI_verified'] == 51 and index['dependencies_unchanged_during_run']
    rows, friendly = [], []
    for source in index['matches']:
        c = json.loads((args.audit_dir / source['analysis_path']).read_text(encoding='utf-8'))
        assert source['audit_status'] == 'verified' and c['gross_ledger_verified']
        assert c['ui_validation']['verified'] and c['provenance']['replay_sha256'] == source['replay_sha256']
        rows.append(row_record(c, {**source, '_folder': str(args.audit_dir)}))
        if c['metrics']['queen_head_collision_relation'] == 'friendly':
            friendly.append(friendly_collision(args.audit_dir / source['replay_path'], c))
    clean = [r for r in rows if r['clean_no_recorded_invalid_action']]
    report = {'generated_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Complete online baseline lifecycle facts; no bot or match execution; no private strategy recovery',
              'audit_index_sha256': sha(index_path), 'analyzer_sha256': sha(Path(__file__)),
              'all_formal': group(rows), 'no_recorded_invalid_action_sensitivity': group(clean),
              'friendly_queen_collisions': friendly, 'matches': rows,
              'phase_definition': 'Fixed official zero-based rounds 0-99, 100-299, 300-terminal; absent later phases have zero samples; every round included',
              'limits': ['Whole-game end-of-round lead uses the official lexicographic score, not hidden intent',
                         'Historical peaks include initial and split-inherited capital; neither autonomous growth nor a counterfactual win',
                         'Cumulative longest-score death drops can later be recovered; not the terminal margin',
                         'Foreign full bodies are replay diagnostics only and are never supplied as bot observations',
                         'Clean subset excludes recorded invalid-action deaths, not proof of all runtime/CPU limits']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise ValueError('Supplement already exists; use a distinct output to preserve evidence')
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'games': len(rows), 'clean': len(clean), 'friendly': len(friendly),
                      'queen_loss_states': report['all_formal']['loss:queen']['terminal_queen_states'],
                      'longest_loss_states': report['all_formal']['loss:longest']['terminal_queen_states']}))


if __name__ == '__main__':
    main()
