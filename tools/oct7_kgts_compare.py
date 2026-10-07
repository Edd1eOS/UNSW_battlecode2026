"""Offline paired KGTS additional-discovery comparison; never launches bots.

Pairs two separately frozen candidates against the same external opponent.
Complete matches and their common end-of-round prefix are separate estimands.
The frozen Oct6 decoders/ledgers are dependencies, not copied implementations.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import json
from pathlib import Path
import re
import statistics
from typing import Any

try:
    from . import audit_online, panel_trajectory, oct7_kgts_panel
except ImportError:
    import audit_online
    import panel_trajectory
    import oct7_kgts_panel


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependencies() -> dict[str, str]:
    folder = Path(__file__).parent
    hashes = {name: digest(folder / name) for name in
              ('oct7_kgts_compare.py', 'oct7_kgts_panel.py', 'oct7_compare_external.py',
               'panel_trajectory.py', 'trajectory_metrics.py', 'audit_online.py')}
    try:
        hashes['official_viewer_archive'] = digest(audit_online._viewer_default())
    except (OSError, ValueError):
        hashes['official_viewer_archive'] = 'unavailable; JSON replay only'
    return hashes


def pair_key(row: dict) -> tuple:
    return row['phase'], row['opponent_id'], row['map'], int(row['seed']), row['candidate_team']


def coverage_frames(data: dict) -> dict[int, dict[str, int | None]]:
    """Movement-head union and actual turn-start geometric window union.

    Split-born heads do not count as successful movement. Windows are sampled
    when an official turn starts, not after each sprint substep. This is no
    claim about reachable tiles, target utility or the bot's private memory.
    """
    match = re.match(r'MAP\s+(\d+)\s+(\d+)', data.get('map', ''))
    size = tuple(map(int, match.groups())) if match else None
    live = {int(d['id']): (d['team'], panel_trajectory.pos(d['body'][0]))
            for d in data['initial_dragons']}
    heads = {t: set() for t in 'AB'}
    windows = {t: set() for t in 'AB'}
    steps = Counter()
    frames, current = {}, None

    def close():
        if current is not None:
            frames[current] = {t: {'successful_updates': steps[t],
                                  'unique_movement_head_cells': len(heads[t]),
                                  'unique_turn_window_cells': len(windows[t]) if size else None}
                               for t in 'AB'}

    for event in data['events']:
        kind = event.get('type', event.get('kind'))
        if kind == 'roundStart':
            close()
            current = int(event['round'])
        elif current is None:
            continue
        elif kind == 'turnStart':
            team, (x, y) = live[int(event['id'])]
            if size:
                w, h = size
                windows[team].update(((x + dx) % w, (y + dy) % h)
                                     for dx in range(-3, 4) for dy in range(-3, 4))
        elif kind == 'dragonUpdate':
            identity = int(event['id'])
            team, _ = live[identity]
            head = panel_trajectory.pos(event['head'])
            live[identity] = team, head
            steps[team] += 1
            heads[team].add(head)
        elif kind == 'dragonSplit':
            parent, child = int(event['parentId']), int(event['childId'])
            team = live[parent][0]
            live[parent] = team, panel_trajectory.pos(event['parentBody'][0])
            live[child] = team, panel_trajectory.pos(event['childBody'][0])
        elif kind == 'dragonDeath':
            del live[int(event['id'])]
    close()
    return frames


def compact_report(report: dict, data: dict) -> dict:
    core, detail, team = report['trajectory'], report['details'], report['candidate_team']
    other = report['opponent_team']
    if not core['quality']['complete_match_verified']:
        raise ValueError('Complete match verification is required')
    coverage = coverage_frames(data)
    worker = {f['round']: f['teams'][team] for f in detail['worker_trajectory']}
    deaths = [d for d in core['deaths'] if d['team'] == team]
    splits = [s for s in core['splits'] if s['team'] == team]
    additions = defaultdict(Counter)
    for d in deaths:
        a = additions[d['round']]
        a['queen_death_length'] += d['last_recorded_length'] if d['is_queen'] else 0
        a['queen_deaths'] += d['is_queen']
        if d['was_unique_longest']:
            a['unique_longest_deaths'] += 1
            a['unique_longest_death_length'] += d['last_recorded_length']
            a['unique_longest_score_loss'] += d['longest_length_loss']
            a['unique_longest_lead_reversals'] += d['reversed_own_lead_immediately']
    for s in splits:
        a = additions[s['round']]
        a['splits'] += 1
        if s['parent_id'] <= 1:
            a['queen_split_transfer'] += s['before_length'] - s['parent_length']
    cumulative = Counter()
    frames = []
    for f in core['trajectory']:
        r = f['round']
        cumulative.update(additions[r])
        own, rival = f['scores'][team], f['scores'][other]
        w = worker[r]
        c = coverage[r][team]
        metrics = dict(own)
        metrics.update(queen_margin=own['queen_length'] - rival['queen_length'],
                       longest_margin=own['longest_dragon'] - rival['longest_dragon'],
                       total_margin=own['total_length'] - rival['total_length'],
                       net_body_update_growth=w['recorded_net_update_growth'],
                       death_length_loss=w['recorded_death_length'],
                       net_retained_length=own['total_length'] - core['initial']['scores'][team]['total_length'],
                       queen_net_retained_length=own['queen_length'] - core['initial']['scores'][team]['queen_length'],
                       food=w['recorded_food'], paid=w['recorded_paid'], **c)
        for name in ('queen_death_length', 'queen_deaths', 'unique_longest_deaths',
                     'unique_longest_death_length', 'unique_longest_score_loss',
                     'unique_longest_lead_reversals', 'splits', 'queen_split_transfer'):
            metrics[name] = cumulative[name]
        metrics['queen_net_update_growth'] = metrics['queen_net_retained_length'] + metrics['queen_death_length'] + metrics['queen_split_transfer']
        if metrics['net_retained_length'] != metrics['net_body_update_growth'] - metrics['death_length_loss']:
            raise ValueError('Compact prefix body balance failed')
        if detail['gross_ledger_verified'] and metrics['food'] - metrics['paid'] != metrics['net_body_update_growth']:
            raise ValueError('Compact prefix gross balance failed')
        frames.append({'round': r, 'leader': 0 if f['leader'] is None else 1 if f['leader'] == team else -1,
                       'criterion': f['criterion'], 'metrics': metrics})
    if detail['gross_ledger_verified']:
        if frames[-1]['metrics']['successful_updates'] != detail['gross_resources'][team]['successful_steps']:
            raise ValueError('Independent coverage update count differs from strict ledger')
    return {k: report[k] for k in ('job_id', 'phase', 'map', 'seed', 'candidate_team', 'opponent_team',
                                  'opponent', 'official_outcome', 'provenance', 'runtime_eligibility',
                                  'eligible_for_mechanism_comparison')} | {
        'gross_ledger_verified': detail['gross_ledger_verified'],
        'gross_ledger_issues': detail['gross_ledger_issues'],
        'queen_gross_resources': {k: detail['gross_resources'][team][k] for k in
                                 ('queen_food_collected', 'queen_paid_step_cost')},
        'terminal': core['final'], 'frames': frames,
        'death_reasons': dict(Counter(d['reason'] for d in deaths)),
        'end_round': frames[-1]['round']}


def analyze_compact(path: Path, row: dict, cache: Path | None, deps: dict) -> dict:
    replay_path = Path(row['replay']['path'])
    if not replay_path.is_absolute():
        replay_path = path.parent / replay_path
    replay_hash = digest(replay_path)
    if replay_hash != row['replay']['sha256']:
        raise ValueError('Replay bytes differ from declared hash')
    binding = {'result_sha256': digest(path), 'replay_sha256': replay_hash, 'dependencies': deps}
    key = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    cache_path = cache / (key + '.json') if cache else None
    if cache_path and cache_path.exists():
        saved = json.loads(cache_path.read_text(encoding='utf-8'))
        if saved['binding'] != binding:
            raise ValueError('Compact cache binding differs')
        return saved['report']
    captured = {}

    def decoder(p):
        captured['data'] = audit_online.load_replay(p)
        return captured['data']

    report = compact_report(panel_trajectory.analyze_result(path, decoder=decoder), captured['data'])
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({'binding': binding, 'report': report}, separators=(',', ':'))+'\n', encoding='utf-8')
    return report


def load_panel(panel: Path, phase: str, cache: Path | None, deps: dict) -> dict:
    if phase not in ('discovery', 'all'):
        raise ValueError('KGTS panels are additional discovery, not holdout')
    plan = oct7_kgts_panel.read_plan(panel)
    freeze = oct7_kgts_panel.candidate_record(panel)
    selected_jobs = {j['id']: j for j in plan['jobs'] if phase == 'all' or j['phase'] == phase}
    rows, failures = [], []
    result_paths = sorted((panel / 'games').rglob('result.json'))
    for path in result_paths:
        try:
            row = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError,OSError) as error:
            failures.append({'result_source':str(path),'job_id':None,'error':str(error)})
            continue
        if phase != 'all' and row['phase'] != phase:
            continue
        stub = {'result_source': str(path), 'job_id': row['id'], 'phase': row['phase'],
                'map': row['map'], 'seed': row['seed'], 'candidate_team': row['candidate_team'],
                'opponent_id': row['id'].split('/')[1], 'official_outcome': row.get('official_outcome'),
                'formal_result': row.get('formal_result'), 'invalid_runtime_events': row.get('invalid_runtime_events'),
                'map_sha256': row['map_sha256'], 'engine_sha256': row['environment']['engine_wasm_sha256'],
                'opponent_source_sha256': row['opponent']['source_bundle_sha256'],
                'opponent_record': row['opponent'], 'environment_record': row['environment'],
                'initial_signature': panel_trajectory.normalized_initial(row['initial_dragons'])}
        stub['candidate_peak_points'] = row['peak'][row['candidate_team']]['points']
        stub['candidate_budget_margin_passed'] = row['candidate_budget_margin_passed']
        try:
            if row['id'] not in selected_jobs:
                raise ValueError('Result not in declared selected schedule')
            job = selected_jobs[row['id']]
            if any(row[k] != job[k] for k in ('phase','map','map_evidence','seed','candidate_team','opponent_team')):
                raise ValueError('Result differs from declared schedule')
            if row['candidate'] != freeze:
                raise ValueError('Result candidate differs from panel freeze')
            if row['map_sha256'] != plan['maps'][row['map']]['sha256']:
                raise ValueError('Result map differs from panel freeze')
            if row['environment'] != plan['environment']:
                raise ValueError('Result environment differs from panel plan')
            if row['opponent'] != plan['opponents'][job['opponent']]:
                raise ValueError('Result opponent differs from panel plan')
            if panel_trajectory.normalized_initial(row['initial_dragons']) != panel_trajectory.normalized_initial(plan['maps'][row['map']]['initial_dragons']):
                raise ValueError('Result initial bodies differ from frozen map')
            stub['report'] = analyze_compact(path, row, cache, deps)
        except (ValueError, KeyError, OSError, RuntimeError) as error:
            stub['analysis_error'] = str(error)
            failures.append({'result_source': str(path), 'job_id': row['id'], 'error': str(error)})
        rows.append(stub)
    return {'panel': str(panel), 'freeze': freeze, 'scheduled': len(selected_jobs),
            'scheduled_missing_results': sorted(set(selected_jobs) - {r['job_id'] for r in rows}),
            'incomplete_attempts': sorted(job_id for job_id in selected_jobs
                                         if (panel / 'games' / job_id).exists()
                                         and not (panel / 'games' / job_id / 'result.json').exists()),
            'completed':sum(bool(r['formal_result'] and r['formal_result'].get('terminated')) for r in rows),
            'result_records':len(rows), 'unscored_results':sum(r['official_outcome'] not in ('win','loss','draw') for r in rows),
            'official_outcomes': dict(Counter(r['official_outcome'] for r in rows if r['official_outcome'] in ('win','loss','draw'))),
            'failures': failures, 'rows': rows}


def view(report: dict, end: int) -> dict:
    frames = [f for f in report['frames'] if f['round'] <= end]
    if not frames or frames[-1]['round'] != end:
        raise ValueError('Common prefix round is not covered')
    values = dict(frames[-1]['metrics'])
    steps = values['successful_updates']
    values['food_per_1000_successful_updates'] = 1000*values['food']/steps if values['food'] is not None and steps else None
    values['net_income_per_1000_successful_updates'] = 1000*(values['food']-values['paid'])/steps if values['food'] is not None and steps else None
    values['net_income'] = values['food']-values['paid'] if values['food'] is not None else None
    for name,value in report['queen_gross_resources'].items():
        values[name] = value if end == report['end_round'] else None
    values['leading_rounds'] = sum(f['leader'] == 1 for f in frames)
    values['lead_losses'] = sum(a['leader'] == 1 and b['leader'] != 1 for a,b in zip(frames,frames[1:]))
    best = streak = 0
    for f in frames:
        streak = streak + 1 if f['leader'] == 1 else 0
        best = max(best, streak)
    values['longest_continuous_lead'] = best
    return {'end_round': end, 'leader': frames[-1]['leader'], 'criterion': frames[-1]['criterion'], 'metrics': values}


GROSS_METRICS = {'food','paid','net_income','food_per_1000_successful_updates','net_income_per_1000_successful_updates',
                 'queen_food_collected','queen_paid_step_cost'}


def compare_panels(baseline: dict, candidate: dict) -> dict:
    indices, conflicts = [], []
    for name, panel in (('baseline', baseline), ('candidate', candidate)):
        index = defaultdict(list)
        for row in panel['rows']:
            index[pair_key(row)].append(row)
        conflicts.extend({'arm': name, 'key': list(k), 'job_ids': [r['job_id'] for r in rr]}
                         for k,rr in index.items() if len(rr) != 1)
        indices.append({k: rr[0] for k,rr in index.items() if len(rr) == 1})
    bi, ci = indices
    pairs, unmatched = [], []
    for key in sorted(set(bi) | set(ci)):
        if key not in bi or key not in ci:
            unmatched.append({'key': list(key), 'missing': 'baseline' if key not in bi else 'candidate'})
            continue
        b, c = bi[key], ci[key]
        issues = []
        for field in ('map_sha256','engine_sha256','environment_record','opponent_source_sha256','opponent_record','initial_signature'):
            if b[field] != c[field]:
                issues.append('Paired environment differs: '+field)
        if 'report' not in b or 'report' not in c:
            issues.append('One or both full replay analyses failed')
        pair = {'key': list(key), 'baseline_result': b['result_source'], 'candidate_result': c['result_source'],
                'baseline_outcome': b['official_outcome'], 'candidate_outcome': c['official_outcome'],
                'baseline_formal_result': b['formal_result'], 'candidate_formal_result': c['formal_result'],
                'baseline_invalid_runtime_events': b['invalid_runtime_events'],
                'candidate_invalid_runtime_events': c['invalid_runtime_events'], 'issues': issues,
                'baseline_candidate_peak_points': b.get('candidate_peak_points'),
                'candidate_peak_points': c.get('candidate_peak_points'),
                'baseline_budget_margin_passed': b.get('candidate_budget_margin_passed'),
                'candidate_budget_margin_passed': c.get('candidate_budget_margin_passed'),
                'eligible_pair': False, 'gross_eligible_pair': False}
        if not issues:
            br, cr = b['report'], c['report']
            pair['eligible_pair'] = all(r['eligible_for_mechanism_comparison'] for r in (br,cr))
            pair['gross_eligible_pair'] = pair['eligible_pair'] and all(r['gross_ledger_verified'] for r in (br,cr))
            pair['baseline_provenance'], pair['candidate_provenance'] = br['provenance'], cr['provenance']
            common = min(br['end_round'], cr['end_round'])
            for label, be, ce in (('whole_match',br['end_round'],cr['end_round']), ('common_prefix',common,common)):
                bv, cv = view(br,be), view(cr,ce)
                delta = {k: cv['metrics'][k] - bv['metrics'][k] for k in bv['metrics']
                         if pair['eligible_pair'] and (k not in GROSS_METRICS or pair['gross_eligible_pair'])
                         and bv['metrics'][k] is not None and cv['metrics'][k] is not None}
                pair[label] = {'baseline': bv, 'candidate': cv, 'eligible_deltas': delta}
            pair['baseline_queen_gross'] = br['queen_gross_resources']
            pair['candidate_queen_gross'] = cr['queen_gross_resources']
            pair['baseline_death_reasons'], pair['candidate_death_reasons'] = br['death_reasons'], cr['death_reasons']
        pairs.append(pair)
    return {'schema_version':1, 'scope':'Paired KGTS additional mechanism discovery; no self matches, no holdout, no independent strength or Elo claim',
            'arms': {name:({k:p[k] for k in ('panel','scheduled','scheduled_missing_results','incomplete_attempts',
                                           'completed','result_records','unscored_results','official_outcomes','failures') if k in p} |
                          {'candidate_source_bundle_sha256':p.get('freeze',{}).get('source_bundle_sha256'),
                           'candidate_wasm_sha256':p.get('freeze',{}).get('wasm_sha256')})
                     for name,p in (('baseline',baseline),('candidate',candidate))},
            'denominators': {'matched_keys':len(pairs), 'environment_and_replay_verified':sum(not p['issues'] for p in pairs),
                             'both_mechanism_eligible':sum(p['eligible_pair'] for p in pairs),
                             'both_eligible_and_gross_verified':sum(p['gross_eligible_pair'] for p in pairs),
                             'unmatched':len(unmatched), 'duplicate_key_conflicts':len(conflicts)},
            'summary': summarize(pairs), 'pairs':pairs, 'unmatched':unmatched, 'duplicate_key_conflicts':conflicts,
            'limits':['Whole-match totals and the common earlier terminal round are separate estimands',
                      'Changing actions changes opponent responses despite the same seed',
                      'Movement-head and geometric turn-window unions do not measure useful food or reachable terrain',
                      'Splits transfer capital; per-step resources require both full strict ledgers and eligibility',
                      'Official outcomes include runtime failures; map/seed/side repeats are correlated']}


def summarize(pairs: list[dict]) -> dict:
    groups = {'all': pairs}
    for p in pairs:
        groups.setdefault('opponent:'+str(p['key'][1]), []).append(p)
        groups.setdefault('map:'+str(p['key'][2]), []).append(p)
    output = {}
    for group, items in groups.items():
        values = {'pairs':len(items),'eligible_pairs':sum(p['eligible_pair'] for p in items),
                  'gross_pairs':sum(p['gross_eligible_pair'] for p in items)}
        for label in ('whole_match','common_prefix'):
            metrics = defaultdict(list)
            for p in items:
                for k,v in p.get(label,{}).get('eligible_deltas',{}).items():
                    metrics[k].append(v)
            values[label] = {k:{'pairs':len(v),'paired_delta_median':statistics.median(v),
                               'paired_delta_mean':statistics.mean(v), 'positive':sum(x>0 for x in v),
                               'zero':sum(x==0 for x in v), 'negative':sum(x<0 for x in v)} for k,v in metrics.items()}
        output[group] = values
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--phase', choices=('discovery','all'), default='discovery')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cache', type=Path, help='Optional hash-bound compact per-replay cache')
    args = parser.parse_args()
    deps = dependencies()
    baseline = load_panel(args.baseline,args.phase,args.cache,deps)
    candidate = load_panel(args.candidate,args.phase,args.cache,deps)
    report = compare_panels(baseline,candidate)
    report['generated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['phase'] = args.phase
    report['actual_scope'] = 'complete' if all(p['completed']==p['scheduled'] and not p['scheduled_missing_results']
                                              for p in (baseline,candidate)) else 'partial'
    report['analyzer_dependencies_sha256'] = deps
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['denominators']))


if __name__ == '__main__':
    main()
