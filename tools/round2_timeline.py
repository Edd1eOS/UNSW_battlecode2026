"""Audit every common-prefix round, with explicit late-checkpoint denominators.

Uses frozen full-replay ledgers and verifies their raw input hashes. No imputed
post-terminal play, opponent execution or bot execution. Descriptive temporal
accounting complements whole-game outcomes; it is not a new adoption threshold.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import oct7_compare_external as primary
import oct7_kgts_compare as kgts

KEYS = ('queen_length', 'queen_margin', 'longest_dragon', 'longest_margin',
        'net_retained_length', 'net_body_update_growth', 'death_length_loss')


def stats(values):
    return {'pairs': len(values), 'mean': statistics.mean(values) if values else None,
            'median': statistics.median(values) if values else None,
            'positive': sum(x > 0 for x in values), 'negative': sum(x < 0 for x in values)}


def build(path, cache, use_kgts=False):
    driver = kgts if use_kgts else primary
    deps = driver.dependencies()
    data = json.loads(path.read_text(encoding='utf-8'))
    assert deps == data['analyzer_dependencies_sha256']
    rows = []
    checkpoints = {r: [] for r in (0, 49, 99, 199, 299, 399, 499)}
    for pair in data['pairs']:
        if pair['issues'] or not pair['gross_eligible_pair']:
            continue
        frames = []
        for arm in ('baseline', 'candidate'):
            result = Path(pair[arm + '_result'])
            assert hashlib.sha256(result.read_bytes()).hexdigest() == pair[arm + '_provenance']['result_json_sha256']
            record = json.loads(result.read_text(encoding='utf-8'))
            compact = driver.analyze_compact(result, record, cache, deps)
            assert compact['provenance'] == pair[arm + '_provenance']
            frames.append({f['round']: f for f in compact['frames']})
        common = sorted(set(frames[0]) & set(frames[1]))
        assert common == list(range(common[-1] + 1))
        deltas = []
        for rd in common:
            b, c = frames[0][rd], frames[1][rd]
            d = {k: c['metrics'][k] - b['metrics'][k] for k in KEYS}
            d['leader_state'] = c['leader'] - b['leader']
            deltas.append(d)
            if rd in checkpoints:
                checkpoints[rd].append(d)
        rows.append({'key': pair['key'], 'common_last_round': common[-1], 'rounds_observed': len(common),
                     'mean_over_actual_common_rounds': {k: statistics.mean(d[k] for d in deltas) for k in (*KEYS, 'leader_state')},
                     'rounds_leader_state_improved': sum(d['leader_state'] > 0 for d in deltas),
                     'rounds_leader_state_worsened': sum(d['leader_state'] < 0 for d in deltas),
                     'checkpoint_deltas': {str(rd): deltas[rd] for rd in checkpoints if rd in common}})
    return {'scope': __doc__, 'matches_run': 0,
            'comparison_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'ledger_dependencies': deps, 'eligible_pairs': len(rows), 'pairs': rows,
            'per_match_temporal_mean_summary': {k: stats([r['mean_over_actual_common_rounds'][k] for r in rows]) for k in (*KEYS, 'leader_state')},
            'checkpoint_summary': {str(rd): {k: stats([d[k] for d in values]) for k in (*KEYS, 'leader_state')}
                                   for rd, values in checkpoints.items()},
            'limits': ['Late checkpoints include only pairs where both actual games reached that round; this is a selected subset.',
                       'Temporal means weight each match equally and summarize actual paired common time, not independent samples.',
                       'Changes in opponent state and response are retained; these are not same-state causal effects.',
                       'Queen and Longest margins are separate. A larger Longest margin is irrelevant to formal victory if Queen already decides.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--kgts',action='store_true')
    args=parser.parse_args()
    report=build(args.comparison,args.cache,args.kgts)
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pairs':report['eligible_pairs'],'temporal_means':report['per_match_temporal_mean_summary']}))
