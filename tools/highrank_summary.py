"""Reproducible descriptive summaries of the frozen 100-game learning cohort."""
import gzip,hashlib,json,statistics
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path('test-results/oct7-highrank-study')

def mean(xs):return round(statistics.mean(xs),3) if xs else None
def main():
    reports=[json.loads(gzip.decompress(p.read_bytes())) for p in sorted((ROOT/'reports').glob('*.json.gz'))]
    source={r['match_id']:r for r in json.loads((ROOT/'resource-provenance.json').read_text())}
    rows=[];teams=defaultdict(list);totals=Counter();phases={k:Counter() for k in ('early','middle','late')}
    losses=Counter();examples=defaultdict(list)
    for r in reports:
        core=r['core'];winner=core['final']['leader'];loser='B' if winner=='A' else 'A';axis=core['final']['criterion']
        score=core['final']['scores'];totals[axis]+=1
        if core['advantage']['by_team'][loser]['leading_rounds']>0:totals['loser_once_led']+=1
        if axis=='queen':
            why='queen_smaller_both_alive' if all(score[t]['queen_length'] for t in 'AB') else 'queen_dead'
        elif axis=='longest':
            peak=max(f['scores'][loser]['longest_dragon'] for f in core['trajectory'])
            why='longest_peak_below_winner_final' if peak<score[winner]['longest_dragon'] else 'longest_capital_lost_or_reallocated'
        else:why='team_eliminated'
        losses[why]+=1;examples[why].append(r['match_id'])
        row={'match_id':r['match_id'],'series':r['metadata']['series'],'map':r['metadata']['text'].split('\n')[1],
             'winner':r['metadata']['teams']['AB'.index(winner)]['name'],'criterion':axis,'loss_class':why,
             'complete_verified':core['quality']['complete_match_verified'],'ui_consistent':r['ui_winner_consistent'],
             'gross_verified':r['details']['gross_ledger_verified'],'sides':{}}
        for i,t in enumerate('AB'):
            c=r['behavior']['counts'][t];ss=[s for s in core['splits'] if s['team']==t];q=r['behavior']['queen_actions'][t]
            alive=score[t]['queen_length']>0;totals['queen_surviving_sides']+=alive
            provenance=source[r['match_id']]['counts'][t]
            side={'name':r['metadata']['teams'][i]['name'],'winner':t==winner,**score[t],
                  'splits':len(ss),'splits_at_length4':sum(s['before_length']==4 for s in ss),
                  'child_length2':sum(s['child_length']==2 for s in ss),'suicide_actions':c.get('suicide',0),
                  'move_actions':c.get('move',0),'multi_step_actions':c.get('multi_step_actions',0),
                  'unique_queen_heads':len({tuple(x['head']) for x in q}),
                  'natural_food':provenance.get('natural',0),
                  'own_recycled_food':provenance.get('own_suicide',0)+provenance.get('own_other_death',0),
                  'enemy_corpse_food':provenance.get('enemy_suicide',0)+provenance.get('enemy_other_death',0),
                  'net_body_growth':core['resources'][t]['recorded_update_net'],
                  'death_length':core['resources'][t]['last_recorded_length_removed_on_death']}
            row['sides'][t]=side;teams[side['name']].append(side)
            for k in ('splits','splits_at_length4','child_length2','suicide_actions','move_actions','multi_step_actions',
                      'natural_food','own_recycled_food','enemy_corpse_food'):totals[k]+=side[k]
            for phase,p in r['behavior']['phases'][t].items():phases[phase].update(p)
        rows.append(row)
    by_team={name:{'games':len(s),'wins':sum(x['winner'] for x in s),
                   'queen_survival':sum(x['queen_length']>0 for x in s),
                   **{k:mean([x[k] for x in s]) for k in ('splits','suicide_actions','queen_length','longest_dragon','dragon_count','natural_food','own_recycled_food')}}
             for name,s in teams.items()}
    out={'games':len(reports),'series':len({r['series'] for r in rows}),'maps':len({r['map'] for r in rows}),
         'teams':len(teams),'complete_verified':sum(r['complete_verified'] for r in rows),
         'ui_consistent':sum(r['ui_consistent'] for r in rows),'gross_verified':sum(r['gross_verified'] for r in rows),
         'resource_origin_verified':sum(not r['issues'] for r in source.values()),'totals':totals,'loss_classes':losses,
         'phase_actions':phases,'by_team':by_team,'matches':rows,
         'limitations':['Convenience/rank-balanced recent-series cohort, not a random sample of all ladder games.',
         'Current rating snapshot is not historical match-time rating. Team version/private source unavailable.',
         'Observational frequencies do not identify causal policy effects. Within-series games are correlated.',
         'Replay suicide action kind does not establish programmer intent or exclude runtime failure.',
         '99/100 strict gross payment ledgers; match1341270 contains a null action and remains unknown.',
         '100 resource-origin event traces reconcile where gross ledger is available; counts include repeated recycling.',
         'Loss classes describe decisive score and trajectory, not a complete causal explanation of each loss.']}
    (ROOT/'summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('matches','by_team','phase_actions')},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
