"""Descriptive sensitivity audit, not another adoption threshold or new games.

All formal outcomes remain. Map-name provenance is a pre-existing label, not
proof that local map bytes or the opponents represent the online population.
"""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('queen_length', 'longest_dragon', 'net_income', 'net_retained_length',
           'queen_net_update_growth', 'queen_deaths', 'lead_losses')


def binding(path):
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def describe(rows):
    eligible = [r for r in rows if r['gross_eligible_pair'] and not r['issues']]
    return {'formal_pairs': len(rows), 'eligible_pairs': len(eligible),
            'outcome_changes': sum(r['baseline_outcome'] != r['candidate_outcome'] for r in rows),
            'whole_match': {k: {
                'mean_delta': statistics.mean(r['whole_match']['eligible_deltas'][k] for r in eligible) if eligible else None,
                'positive': sum(r['whole_match']['eligible_deltas'][k] > 0 for r in eligible),
                'negative': sum(r['whole_match']['eligible_deltas'][k] < 0 for r in eligible)} for k in METRICS},
            'queen_gain_pairs': [r['key'] for r in eligible if r['whole_match']['eligible_deltas']['queen_length'] > 0],
            'changed_pairs': [{'key': r['key'], 'whole_delta': {k: r['whole_match']['eligible_deltas'][k] for k in METRICS},
                               'prefix_delta': {k: r['common_prefix']['eligible_deltas'][k] for k in METRICS}}
                              for r in eligible if any(r['whole_match']['eligible_deltas'][k] for k in METRICS)]}


def main():
    reports = []
    for name in ('evidence', 'topology', 'topology-v2', 'resource', 'resource-v2'):
        for extra in ('', '-kgts'):
            if name == 'evidence' and extra:
                continue
            path = ROOT / f'test-results/round2-{name}{extra}-compare.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            assert data['actual_scope'] == 'complete'
            plan_path = ROOT / f'test-results/round2-{name}{extra}-panel/plan.json'
            wrapped = json.loads(plan_path.read_text(encoding='utf-8'))
            plan = wrapped['plan']
            groups = {'all': data['pairs']}
            for r in data['pairs']:
                groups.setdefault('opponent:' + r['key'][1], []).append(r)
                groups.setdefault('map_provenance:' + plan['maps'][r['key'][2]]['map_evidence'], []).append(r)
            reports.append({'name': name + extra, 'comparison': binding(path), 'plan': binding(plan_path),
                            'groups': {key: describe(rows) for key, rows in groups.items()}})
    out = ROOT / 'docs/oct7-round2-generalization.json'
    out.write_text(json.dumps({'scope': __doc__, 'driver': binding(Path(__file__)), 'matches_run': 0,
                               'reports': reports,
                               'limits': ['Repeated arms are correlated; groups must not be pooled as independent matches.',
                                          'Queen benefit locations are post-outcome descriptions, not held-out confirmation.',
                                          'This reduction relies on the hash-bound strict comparisons; the bounded manifest verifies their raw input bytes.']},
                              ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'reports': len(reports), 'output': binding(out)}))


if __name__ == '__main__':
    main()
