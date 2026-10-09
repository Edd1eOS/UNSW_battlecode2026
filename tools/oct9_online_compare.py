"""Compare summary measurements from two real-online map panels, not local matches."""
import argparse
import json
from pathlib import Path


def panel(path, bot_id):
    raw = json.loads(path.read_text())
    games = {}
    for row in raw:
        own = [t for t, team in row['teams'].items() if str(team.get('botId')) == str(bot_id)]
        if len(own) != 1:
            raise ValueError(f'Expected one own submission {bot_id}: {row["teams"]}')
        team = own[0]
        s = row['stats'][team]
        name = row['map']
        if name in games:
            raise ValueError(f'Duplicate map name {name}')
        summary = s['summary']
        games[name] = {'replay': row['path'], 'own_team': team,
                       'result': 'D' if row['result']['winner'] is None else 'W' if row['result']['winner'] == team else 'L',
                       'queen_length_final': s['final']['queenLength'],
                       'queen_deaths': summary['queen_deaths'],
                       'longest_final': s['final']['longestDragon'],
                       'total_length_final': s['final']['totalLength'],
                       'queen_move_net_growth': s['queen_food'] - s['queen_paid'],
                       'queen_shed_to_children': s['queen_shed_to_children'],
                       'unit_turns': s['unit_turns'], 'long_turns': s['long_turns'],
                       'long_head_deaths_enemy_turn': summary['long_head_deaths_enemy_turn'],
                       'long_head_length_lost_enemy_turn': summary['long_head_length_lost_enemy_turn'],
                       'emergency_splits': summary['emergency_splits'],
                       'emergency_parent_dies_within_two_rounds': summary['emergency_parent_dies_within_two_rounds'],
                       'total_splits': summary['total_splits'],
                       'instruction_peak': s['instruction_peak'],
                       'instruction_exceeded': s['instruction_exceeded'], 'null_actions': s['null_actions'],
                       'snapshots': s['snapshots']}
    n = len(games)
    total = {key: sum(g[key] for g in games.values()) for key in
             ('unit_turns', 'long_turns', 'long_head_deaths_enemy_turn', 'long_head_length_lost_enemy_turn',
              'emergency_splits', 'emergency_parent_dies_within_two_rounds', 'total_splits',
              'instruction_exceeded', 'null_actions')}
    total.update(games=n, wins=sum(g['result'] == 'W' for g in games.values()),
                 draws=sum(g['result'] == 'D' for g in games.values()),
                 losses=sum(g['result'] == 'L' for g in games.values()),
                 queens_alive_final=sum(g['queen_length_final'] > 0 for g in games.values()),
                 mean_queen_length_final=sum(g['queen_length_final'] for g in games.values()) / max(1, n),
                 mean_longest_final=sum(g['longest_final'] for g in games.values()) / max(1, n),
                 instruction_peak=max((g['instruction_peak'] for g in games.values()), default=0))
    total['emergency_splits_per_1000_unit_turns'] = 1000 * total['emergency_splits'] / max(1, total['unit_turns'])
    total['long_head_deaths_per_1000_long_turns'] = 1000 * total['long_head_deaths_enemy_turn'] / max(1, total['long_turns'])
    return {'source_audit': str(path), 'submission': bot_id, 'summary': total, 'games': games}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--baseline-id', required=True)
    p.add_argument('--candidate-id', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    baseline = panel(a.baseline, a.baseline_id)
    candidate = panel(a.candidate, a.candidate_id)
    matching = sorted(baseline['games'].keys() & candidate['games'].keys())
    result = {'baseline': baseline, 'candidate': candidate,
              'same_map_set': set(baseline['games']) == set(candidate['games']),
              'matching_maps': matching,
              'scope': 'Both panels are actual online matches. Same opponent display name and map set do not control random seeds, spawn side, or private opponent version. Outcome comparisons are descriptive, not a controlled win-rate or rating effect estimate.'}
    a.out.write_text(json.dumps(result, indent=2))
    print(json.dumps({'baseline': baseline['summary'], 'candidate': candidate['summary'], 'same_map_set': result['same_map_set']}, indent=2))
