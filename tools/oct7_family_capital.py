"""Offline disjoint-founder and post-split capital audit.

No engines or bots run. A split transfers capital, not income. Gross resources
come only from the frozen strict ledger; this reducer measures body deltas.
Post-split cohorts overlap and are never summed as independent investments.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics

try:
    from . import audit_online, panel_trajectory, trajectory_metrics
except ImportError:
    import audit_online, panel_trajectory, trajectory_metrics


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dependencies():
    directory = Path(__file__).parent
    result = {name: sha(directory / name) for name in
              ('oct7_family_capital.py', 'audit_online.py', 'panel_trajectory.py', 'trajectory_metrics.py')}
    result['official_viewer_archive'] = sha(audit_online._viewer_default())
    return result


def audit_families(data, core, detail):
    if not core['quality']['complete_match_verified'] or data.get('input_format') == 'text_log':
        raise ValueError('Full verified body replay is required')
    initial = {int(d['id']): d for d in data['initial_dragons']}
    body = {i: [panel_trajectory.pos(p) for p in d['body']] for i, d in initial.items()}
    lives, children, founders = {}, defaultdict(list), {}
    for i, d in initial.items():
        founders[i] = {'team': d['team'], 'initial_body': body[i].copy(), 'initial_capital': len(body[i])}
        lives[i] = {'team': d['team'], 'founder': i, 'parent': None, 'birth_event': -1,
                    'states': [(-1, len(body[i]))], 'updates': [], 'death': None}
    net, loss, split_counts = Counter(), Counter(), Counter()
    indicators = {}
    core_frames = {f['round']: f for f in core['trajectory']}
    strict_frames = {f['round']: f for f in detail['worker_trajectory']}
    frames, splits = [], []
    current = None

    def close(end_event):
        if current is None:
            return
        family = {}
        for root, meta in founders.items():
            lengths = [len(b) for i, b in body.items() if lives[i]['founder'] == root]
            total = sum(lengths)
            queen = len(body[root]) if root <= 1 and root in body else 0
            if total != meta['initial_capital'] + net[root] - loss[root]:
                raise ValueError('Founder capital balance failed')
            family[root] = {'total_length': total, 'dragon_count': len(lengths), 'queen_length': queen,
                            'longest_dragon': max(lengths, default=0), 'net_update_growth': net[root],
                            'death_length_loss': loss[root], 'splits': split_counts[root],
                            'net_retained': total - meta['initial_capital']}
        teams = {}
        for t in 'AB':
            fs = [v for i, v in family.items() if founders[i]['team'] == t]
            lengths = [len(b) for i, b in body.items() if lives[i]['team'] == t]
            total = sum(lengths)
            teams[t] = {'total_length': total, 'dragon_count': len(lengths),
                        'queen_length': max((v['queen_length'] for v in fs), default=0),
                        'longest_dragon': max(lengths, default=0),
                        'net_update_growth': sum(v['net_update_growth'] for v in fs),
                        'death_length_loss': sum(v['death_length_loss'] for v in fs),
                        'largest_unit_share': max(lengths, default=0) / total if total else None,
                        'squared_length_share': sum(n*n for n in lengths) / (total*total) if total else None}
            official = core_frames[current]['scores'][t]
            if any(teams[t][key] != official[key] for key in ('total_length', 'dragon_count', 'queen_length', 'longest_dragon')):
                raise ValueError('Family state differs from frozen complete round state')
            recorded = strict_frames[current]['teams'][t]
            if (teams[t]['net_update_growth'] != recorded['recorded_net_update_growth']
                    or teams[t]['death_length_loss'] != recorded['recorded_death_length']):
                raise ValueError('Family flows differ from frozen complete round ledger')
        frames.append({'round': current, 'end_event': end_event, 'families': family, 'teams': teams})

    for index, e in enumerate(data['events']):
        kind = e.get('type', e.get('kind'))
        if kind == 'roundStart':
            close(index - 1)
            current = int(e['round'])
        elif current is None:
            continue
        elif kind == 'turnStart':
            indicators[int(e['id'])] = None
        elif kind == 'dragonIndicator':
            indicators[int(e['id'])] = e.get('text')
        elif kind == 'dragonUpdate':
            i = int(e['id'])
            previous = len(body[i])
            updated = [panel_trajectory.pos(e['head']), *body[i]]
            tail = panel_trajectory.pos(e['tail'])
            while len(updated) > 1 and updated[-1] != tail:
                updated.pop()
            if updated[-1] != tail:
                raise ValueError('Tail absent from family body')
            body[i] = updated
            change = len(updated) - previous
            net[lives[i]['founder']] += change
            lives[i]['updates'].append((index, change))
            lives[i]['states'].append((index, len(updated)))
        elif kind == 'dragonSplit':
            parent, child = int(e['parentId']), int(e['childId'])
            old = len(body[parent])
            pb = [panel_trajectory.pos(p) for p in e['parentBody']]
            cb = [panel_trajectory.pos(p) for p in e['childBody']]
            if child in lives or e['team'] != lives[parent]['team']:
                raise ValueError('Split lineage identity/team changed')
            if pb + list(reversed(cb)) != body[parent]:
                raise ValueError('Split does not partition and reverse the recorded parent body')
            root = lives[parent]['founder']
            body[parent], body[child] = pb, cb
            lives[parent]['states'].append((index, len(pb)))
            lives[child] = {'team': e['team'], 'founder': root, 'parent': parent, 'birth_event': index,
                            'states': [(index, len(cb))], 'updates': [], 'death': None}
            children[parent].append(child)
            split_counts[root] += 1
            indicator = indicators.get(parent)
            forecasts = {k: float(v) for k,v in re.findall(r'\b(joint_food_est|joint_paid_est|joint_complete|joint_unknown|joint_budget|joint_pruned|joint_nodes|explore_est)=([-+0-9.eE]+)', indicator or '')}
            splits.append({'round': current, 'event_index': index, 'team': e['team'], 'founder': root,
                           'parent_id': parent, 'child_id': child, 'capital_before': old,
                           'parent_after': len(pb), 'child_birth_capital': len(cb),
                           'decision_indicator': indicator, 'reported_forecast': forecasts})
        elif kind == 'dragonDeath':
            i = int(e['id'])
            length = len(body.pop(i))
            loss[lives[i]['founder']] += length
            lives[i]['death'] = {'event_index': index, 'round': current, 'length': length, 'reason': e.get('reason')}
            lives[i]['states'].append((index, 0))
    close(len(data['events']) - 1)
    if len(frames) != len(core['trajectory']):
        raise ValueError('Family round coverage differs')
    strict_lives = {d['id']: d for d in detail['dragons']}
    for i, life in lives.items():
        recorded = strict_lives[i]
        if (sum(v for _, v in life['updates']) != recorded['net_update_growth']
                or life['states'][-1][1] != recorded['final_length']
                or life['parent'] != recorded['birth_parent']):
            raise ValueError('Life state/lineage differs from strict lifecycle ledger')
        times, cumulative = [], [0]
        for ix, change in life['updates']:
            times.append(ix)
            cumulative.append(cumulative[-1] + change)
        life['update_times'], life['update_sums'] = times, cumulative
        life['state_times'] = [ix for ix, _ in life['states']]

    def state_at(i, end):
        life = lives[i]
        index = bisect_right(life['state_times'], end) - 1
        return life['states'][index][1] if index >= 0 else 0

    def update_sum(i, end):
        life = lives[i]
        return life['update_sums'][bisect_right(life['update_times'], end)]

    def cohort(split, end):
        start = split['event_index']
        members, pending = set(), [split['parent_id']]
        while pending:
            i = pending.pop()
            members.add(i)
            pending.extend(c for c in children[i] if start <= lives[c]['birth_event'] <= end)
        if split['child_id'] not in members:
            raise ValueError('New child absent from its investment cohort')
        income = sum(update_sum(i, end) - update_sum(i, start) for i in members)
        death = sum(lives[i]['death']['length'] for i in members if lives[i]['death']
                    and start < lives[i]['death']['event_index'] <= end)
        lengths = [state_at(i, end) for i in members]
        total = sum(lengths)
        if total != split['capital_before'] + income - death:
            raise ValueError('Post-split cohort capital balance failed')
        return {'descendant_count': len(members), 'live_count': sum(n > 0 for n in lengths),
                'retained_capital': total, 'net_update_growth': income, 'death_length_loss': death,
                'net_retained': total - split['capital_before'], 'longest': max(lengths),
                'food': None, 'paid': None}

    end_frames = {f['round']: f for f in frames}
    for split in splits:
        target = split['round'] + 1  # Current child turn plus the next complete round.
        end = min(target, frames[-1]['round'])
        split['two_round'] = cohort(split, end_frames[end]['end_event'])
        split['two_round'].update(end_round=end, requested_end_round=target, truncated=end != target)
        split['whole_after_split'] = cohort(split, frames[-1]['end_event'])
        forecast = split['reported_forecast']
        split['reported_forecast_net'] = (forecast['joint_food_est'] - forecast['joint_paid_est']
                                         if forecast.get('joint_complete') == 1 and
                                         {'joint_food_est','joint_paid_est'} <= forecast.keys() else None)

    families = []
    for root, meta in founders.items():
        ids = [i for i, life in lives.items() if life['founder'] == root]
        final = dict(frames[-1]['families'][root])
        final['food'] = sum(strict_lives[i]['food'] for i in ids) if detail['gross_ledger_verified'] else None
        final['paid'] = sum(strict_lives[i]['paid'] for i in ids) if detail['gross_ledger_verified'] else None
        if final['food'] is not None and final['food'] - final['paid'] != final['net_update_growth']:
            raise ValueError('Founder gross balance failed')
        families.append({'founder_id': root, **meta, 'lifetime_count': len(ids), 'terminal': final})
    phases = []
    for frame_index, frame in enumerate(frames):
        state = ''.join(t for t in 'AB' if frame['teams'][t]['queen_length'] > 0) or 'none'
        if not phases or phases[-1]['queens_alive'] != state:
            phases.append({'queens_alive': state, 'start_round': frame['round'], 'end_round': frame['round'],
                           'family_net_update_growth': Counter(), 'family_death_length': Counter(),
                           'family_splits': Counter()})
        phase = phases[-1]
        phase['end_round'] = frame['round']
        previous = frames[frame_index - 1] if frame_index else None
        for root, values in frame['families'].items():
            before = previous['families'][root] if previous else {}
            for source, dest in (('net_update_growth', 'family_net_update_growth'), ('death_length_loss', 'family_death_length'), ('splits', 'family_splits')):
                phase[dest][root] += values[source] - before.get(source, 0)
        phase['ending_families'] = frame['families']
    return {'initial_signature': panel_trajectory.normalized_initial(data['initial_dragons']),
            'gross_ledger_verified': detail['gross_ledger_verified'], 'rounds_verified': len(frames),
            'families': families, 'frames': frames, 'queen_state_phases': phases, 'splits': splits,
            'limits': ['Founders are disjoint; later child IDs are not aligned across different games',
                       'Post-split cohorts exclude earlier children; overlapping cohorts must not be summed',
                       'Two-round cohorts end after the birth round and the following complete round',
                       'Family-phase and post-split gross are unknown; net is a verified body-delta account',
                       'Queen phases use ending round state and include the transition round in its new phase',
                       'A post-split gain is observed retention, not a no-split causal counterfactual']}


def analyze_path(path, cache=None):
    path = Path(path)
    row = json.loads(path.read_text(encoding='utf-8'))
    replay = Path(row['replay']['path'])
    if not replay.is_absolute():
        replay = path.parent / replay
    if sha(replay) != row['replay']['sha256']:
        raise ValueError('Replay bytes differ from declared hash')
    binding = {'result_sha256': sha(path), 'replay_sha256': sha(replay), 'dependencies': dependencies()}
    key = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    cache_path = Path(cache) / (key + '.json') if cache else None
    if cache_path and cache_path.exists():
        saved = json.loads(cache_path.read_text(encoding='utf-8'))
        if saved['binding'] != binding:
            raise ValueError('Family cache binding differs')
        return saved['report']
    capture = {}
    def decode(raw):
        capture['data'] = audit_online.load_replay(raw)
        return capture['data']
    strict = panel_trajectory.analyze_result(path, decoder=decode)
    family = audit_families(capture['data'], strict['trajectory'], strict['details'])
    family.update(provenance=strict['provenance'], binding=binding, candidate_team=strict['candidate_team'],
                  eligible=strict['eligible_for_mechanism_comparison'], official_outcome=strict['official_outcome'])
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({'binding': binding, 'report': family}, separators=(',', ':'))+'\n', encoding='utf-8')
    return family


def compare_family_reports(baseline, candidate):
    """Align only the unchanged initial founders, never later engine IDs."""
    if (json.dumps(baseline['initial_signature']) != json.dumps(candidate['initial_signature'])
            or baseline['candidate_team'] != candidate['candidate_team']):
        raise ValueError('Founder initial body/team alignment differs')
    eligible = baseline['eligible'] and candidate['eligible']
    gross = eligible and baseline['gross_ledger_verified'] and candidate['gross_ledger_verified']
    team = baseline['candidate_team']
    common = min(baseline['frames'][-1]['round'], candidate['frames'][-1]['round'])
    output = {'eligible': eligible, 'gross_eligible': gross, 'common_end_round': common, 'families': []}
    for b in baseline['families']:
        if b['team'] != team:
            continue
        c = next(f for f in candidate['families'] if f['founder_id'] == b['founder_id'])
        root = str(b['founder_id'])
        item = {'founder_id': b['founder_id'], 'initial_capital': b['initial_capital']}
        for label in ('whole_match', 'common_prefix'):
            if label == 'whole_match':
                bv, cv = b['terminal'], c['terminal']
            else:
                bf = next(f for f in baseline['frames'] if f['round'] == common)
                cf = next(f for f in candidate['frames'] if f['round'] == common)
                bv = next(v for i,v in bf['families'].items() if str(i) == root)
                cv = next(v for i,v in cf['families'].items() if str(i) == root)
            item[label] = {'baseline': bv, 'candidate': cv, 'eligible_deltas': {
                k: cv[k] - v for k,v in bv.items() if eligible and v is not None and cv[k] is not None
                and (k not in ('food','paid') or gross)}}
        output['families'].append(item)
    for name, report in (('baseline', baseline), ('candidate', candidate)):
        own = [s for s in report['splits'] if s['team'] == team]
        values = {}
        for label in ('two_round','whole_after_split'):
            selected = [s[label] for s in own if label != 'two_round' or not s[label]['truncated']]
            values[label] = {'cohorts': len(selected), 'omitted_truncated': len(own)-len(selected)}
            for key in ('net_update_growth','death_length_loss','net_retained','longest'):
                vv = [s[key] for s in selected]
                values[label][key] = {'median': statistics.median(vv) if vv else None,
                                     'mean': statistics.mean(vv) if vv else None,
                                     'positive': sum(v>0 for v in vv), 'zero': sum(v==0 for v in vv),
                                     'negative': sum(v<0 for v in vv)}
        output[name+'_cohort_summary'] = values
        forecasts = [s for s in own if s['reported_forecast_net'] is not None and not s['two_round']['truncated']]
        errors = [s['two_round']['net_update_growth'] - s['reported_forecast_net'] for s in forecasts]
        output[name+'_forecast_observations'] = {
            'complete_nontruncated_forecasts': len(forecasts),
            'actual_two_round_net_minus_reported_estimate_median': statistics.median(errors) if errors else None,
            'actual_two_round_net_minus_reported_estimate_mean': statistics.mean(errors) if errors else None,
            'below_estimate': sum(x<0 for x in errors), 'at_estimate': sum(x==0 for x in errors), 'above_estimate': sum(x>0 for x in errors),
            'basis': 'Bot indicator estimates, not official guarantees; actual descendants and environment may differ'}
        output[name+'_queen_state_phases'] = report['queen_state_phases']
        output[name+'_terminal_concentration'] = report['frames'][-1]['teams'][team]
    output['cohort_warning'] = 'Within each arm cohorts overlap, have different births and are not causal paired ROI samples'
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--result', type=Path)
    mode.add_argument('--comparison', type=Path, help='Existing strict paired report; preserves its exact scope')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    args = parser.parse_args()
    if args.result:
        report = analyze_path(args.result, args.cache)
    else:
        comparison = json.loads(args.comparison.read_text(encoding='utf-8'))
        report = {'comparison_source': str(args.comparison), 'comparison_sha256': sha(args.comparison),
                  'actual_scope': comparison['actual_scope'], 'dependencies': dependencies(),
                  'pairs': [], 'failures': [], 'ineligible_preserved': []}
        for pair in comparison['pairs']:
            if not pair['eligible_pair']:
                report['ineligible_preserved'].append({'key': pair['key'], 'baseline_outcome': pair['baseline_outcome'],
                                                       'candidate_outcome': pair['candidate_outcome'], 'issues': pair['issues']})
                continue
            try:
                arms = []
                for arm in ('baseline','candidate'):
                    value = analyze_path(pair[arm+'_result'], args.cache)
                    if value['provenance'] != pair[arm+'_provenance']:
                        raise ValueError('Result/replay provenance differs from input paired report')
                    arms.append(value)
                report['pairs'].append({'key': pair['key'], **compare_family_reports(*arms)})
            except (OSError, ValueError, RuntimeError, KeyError) as error:
                report['failures'].append({'key': pair['key'], 'error': str(error)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'rounds_verified': report['rounds_verified'], 'families': len(report['families']), 'splits': len(report['splits'])}
                     if args.result else {'paired_family_reports': len(report['pairs']), 'failures': len(report['failures'])}))


if __name__ == '__main__':
    main()
