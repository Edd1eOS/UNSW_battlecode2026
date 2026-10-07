"""Read a strict paired report in official lexicographic scoring context.

No replay, engine or candidate is changed. Absolute Longest changes are not
treated as the deciding criterion when Queen or elimination decides first.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

try:
    from . import trajectory_metrics
except ImportError:
    import trajectory_metrics


def context(formal, own_team):
    if not formal.get('terminated'):
        raise ValueError('Terminated formal result is required')
    score = {t: {dst: int(formal['team'+t][src]) for src,dst in
                 (('dragonCount','dragon_count'),('queenLength','queen_length'),
                  ('longestDragon','longest_dragon'),('totalLength','total_length'))} for t in 'AB'}
    decision = trajectory_metrics.advantage(score)
    if decision['leader'] != formal['winner']:
        raise ValueError('Formal winner differs from verified lexicographic state')
    other = 'B' if own_team == 'A' else 'A'
    own, rival = score[own_team], score[other]
    both_live = bool(own['dragon_count'] and rival['dragon_count'])
    queen_equal = own['queen_length'] == rival['queen_length']
    qm = own['queen_length'] - rival['queen_length']
    return {'axis': decision['criterion'], 'queen_equal': queen_equal, 'both_teams_present': both_live,
            'longest_rule_reached': both_live and queen_equal,
            'queen_relation': 'equal' if qm == 0 else 'own_greater' if qm > 0 else 'rival_greater',
            'queen_margin': qm, 'longest_margin': own['longest_dragon'] - rival['longest_dragon'],
            'total_margin': own['total_length'] - rival['total_length'], 'own': own, 'rival': rival,
            'outcome': 'draw' if decision['leader'] is None else 'win' if decision['leader'] == own_team else 'loss'}


def stats(values):
    return {'pairs':len(values), 'paired_delta_median':statistics.median(values) if values else None,
            'paired_delta_mean':statistics.mean(values) if values else None,
            'positive':sum(x>0 for x in values), 'zero':sum(x==0 for x in values), 'negative':sum(x<0 for x in values)}


def build(report):
    rows, issues = [], []
    for p in report['pairs']:
        try:
            b=context(p['baseline_formal_result'],p['key'][4])
            c=context(p['candidate_formal_result'],p['key'][4])
            if b['outcome'] != p['baseline_outcome'] or c['outcome'] != p['candidate_outcome']:
                raise ValueError('Formal outcome differs from paired report')
            row = {'key':p['key'], 'eligible_pair':p['eligible_pair'], 'baseline':b, 'candidate':c,
                   'both_longest_rule_reached':b['longest_rule_reached'] and c['longest_rule_reached'],
                   'both_queen_decided':b['axis'] == c['axis'] == 'queen',
                   'longest_margin_delta':c['longest_margin']-b['longest_margin'],
                   'queen_margin_delta':c['queen_margin']-b['queen_margin'],
                   'absolute_own_longest_delta':c['own']['longest_dragon']-b['own']['longest_dragon']}
            rows.append(row)
        except (KeyError,ValueError,TypeError) as error:
            issues.append({'key':p['key'],'error':str(error)})
    scopes = {}
    for scope, selected in (('all_formal',rows),('paired_eligible',[r for r in rows if r['eligible_pair']])):
        longest = [r for r in selected if r['both_longest_rule_reached']]
        queen = [r for r in selected if r['both_queen_decided']]
        scopes[scope] = {'pairs':len(selected),
            'axis_transitions':dict(Counter(r['baseline']['axis']+' -> '+r['candidate']['axis'] for r in selected)),
            'queen_relation_transitions':dict(Counter(r['baseline']['queen_relation']+' -> '+r['candidate']['queen_relation'] for r in selected)),
            'longest_rule_both_arms':{'pairs':len(longest),
                 'own_longest_delta':stats([r['absolute_own_longest_delta'] for r in longest]),
                 'own_minus_rival_longest_margin_delta':stats([r['longest_margin_delta'] for r in longest])},
            'queen_decided_both_arms':{'pairs':len(queen),'queen_margin_delta':stats([r['queen_margin_delta'] for r in queen])},
            'queen_relation_or_axis_changed':[r['key'] for r in selected if r['baseline']['queen_relation']!=r['candidate']['queen_relation']
                                             or r['baseline']['axis']!=r['candidate']['axis']]}
    return {'actual_scope':report['actual_scope'],'summaries':scopes,'pairs':rows,'issues':issues,
            'limits':['Terminal scoring context is descriptive, not a new adoption gate',
                      'All formal results remain; runtime-eligible subset is separate',
                      'When both Queens tie and both teams remain, Longest is reached even if its tie proceeds to Total',
                      'Subset with the same reached axis in both arms is selected after outcomes; never replaces main denominator',
                      'Queen trades change opponent state and future behavior; margin changes do not establish causal superiority']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    raw=args.comparison.read_bytes();report=build(json.loads(raw))
    report.update(comparison_source=str(args.comparison),comparison_sha256=hashlib.sha256(raw).hexdigest(),
                  scoring_context_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  frozen_scoring_dependency_sha256=hashlib.sha256(Path(trajectory_metrics.__file__).read_bytes()).hexdigest())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['summaries']['paired_eligible']))


if __name__=='__main__':
    main()
