"""Describe what the frozen external discovery opponents actually exercise.

No extra matches, opponent modifications, or adoption threshold changes.
Outcome exposure is descriptive and conditioned on both arms being eligible.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def binding(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    comparisons = [ROOT / f'test-results/round2-resource-v2{suffix}-compare.json' for suffix in ('', '-kgts')]
    groups = []
    for path in comparisons:
        report = json.loads(path.read_text(encoding='utf-8'))
        assert report['actual_scope'] == 'complete'
        for opponent in sorted({r['key'][1] for r in report['pairs']}):
            all_rows = [r for r in report['pairs'] if r['key'][1] == opponent]
            eligible = [r for r in all_rows if r['eligible_pair'] and not r['issues']]
            group = {'opponent': opponent, 'comparison': binding(path), 'formal_pairs': len(all_rows),
                     'eligible_pairs': len(eligible), 'ineligible_pairs': len(all_rows) - len(eligible)}
            for arm in ('baseline', 'candidate'):
                frames = [r['whole_match'][arm] for r in eligible]
                group[arm] = {'eligible_outcomes': dict(Counter(r[arm + '_outcome'] for r in eligible)),
                              'terminal_scoring_axes': dict(Counter(f['criterion'] for f in frames)),
                              'rival_queen_alive': sum(f['metrics']['queen_length'] - f['metrics']['queen_margin'] > 0 for f in frames),
                              'both_queens_alive': sum(f['metrics']['queen_length'] > 0 and f['metrics']['queen_length'] - f['metrics']['queen_margin'] > 0 for f in frames),
                              'queen_alive_pair_keys': [r['key'] for r in eligible
                                  if r['whole_match'][arm]['metrics']['queen_length'] > 0
                                  and r['whole_match'][arm]['metrics']['queen_length'] - r['whole_match'][arm]['metrics']['queen_margin'] > 0]}
            groups.append(group)
    files = [ROOT / name for name in ('external-benchmarks/sas-987/main.cpp',
             'external-benchmarks/official-murder/main.cpp',
             'external-benchmarks/kgts-protocol-adapted/source/main.py')]
    out = ROOT / 'docs/oct7-round2-benchmark-audit.json'
    out.write_text(json.dumps({'scope': __doc__, 'driver': binding(Path(__file__)), 'matches_run': 0,
                               'frozen_source_read': [binding(p) for p in files], 'groups': groups,
                               'limits': ['A terminal Queen exposure count does not measure all intermediate Queen threats.',
                                          'The same maps and opponents recur; these are not independent representative ladder samples.',
                                          'Weak frozen opponents remain useful regressions but do not establish stronger live-opponent performance.',
                                          'No missing or ineligible match is converted into a reliable strength observation.']},
                              ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'groups': len(groups), 'out': binding(out)}))


if __name__ == '__main__':
    main()
