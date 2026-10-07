"""Publish the fixed 100-game learning cohort; no new games or source changes."""
from collections import Counter,defaultdict
import gzip,hashlib,json,statistics
from pathlib import Path

ROOT=Path('test-results/oct7-highrank-study')
DOC=Path('docs')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def mean(xs):return round(statistics.mean(xs),3) if xs else None
def main():
    summary=read(ROOT/'summary.json');imports={r['match_id']:r for r in read(ROOT/'imports.json')}
    assert summary['games']==100 and summary['complete_verified']==summary['ui_consistent']==100
    source={r['match_id']:r for r in read(ROOT/'resource-provenance.json')}
    teams=defaultdict(list);games=[];deaths=Counter();same_side_metrics=defaultdict(list)
    for row in summary['matches']:
        i=row['match_id'];path=ROOT/'reports'/f'M{i}.json.gz';report=json.loads(gzip.decompress(path.read_bytes()))
        core=report['core'];queen={d['team']:d for d in report['details']['dragons'] if d['is_queen']}
        for t in 'AB':
            side=row['sides'][t];q=queen[t];orig=source[i]['counts'][t]
            worker=[d for d in report['details']['dragons'] if d['team']==t and not d['is_queen']]
            late=report['behavior']['phases'][t]['late'];initial=report['behavior']['phases'][t]['early']
            small=sum(x['team']==t and x['length'] in (2,3) for x in report['behavior']['suicides'])
            additions={'queen_death':q['death'],'queen_food':q['food'],
                       'queen_natural_food':orig.get('queen_natural',0),
                       'queen_own_corpse_food':orig.get('queen_own_suicide',0)+orig.get('queen_own_other_death',0),
                       'queen_own_recorded_suicide_food':orig.get('queen_own_suicide',0),
                       'small_suicide_actions':small,'worker_peak':max((d['peak_length'] for d in worker),default=0),
                       'early_splits_per_100_actions':100*initial.get('split',0)/max(1,initial.get('actions',0)),
                       'late_splits_per_100_actions':100*late.get('split',0)/max(1,late.get('actions',0)),
                       'queen_splits':len([s for s in core['splits'] if s['team']==t and s['parent_id']<=1])}
            side.update(additions);teams[side['name']].append(side)
            if q['death']:deaths[q['death']['reason']]+=1
            for snapshot in (99,199,299,399):
                frame=next((f for f in core['trajectory'] if f['round']==snapshot),None)
                if frame and side['winner']:
                    same_side_metrics[str(snapshot)].append(frame['leader']==t)
        games.append({**row,'url':f'https://game.battlecode.au/battles/{i}',
                      'raw_sha256':sha(ROOT/'raw'/f'M{i}.replay'),'report_sha256':sha(path),
                      'decoder_sha256':report['decoder_sha256'],'imports':imports[i],
                      'resource_origin':source[i],
                      'gross_issues':report['details']['gross_ledger_issues'],
                      'lead_history':core['advantage']})
    by_team={name:{'games':len(xs),'wins':sum(x['winner'] for x in xs),'queen_survives':sum(x['queen_length']>0 for x in xs),
        **{k+'_mean':mean([x[k] for x in xs]) for k in ('splits','queen_length','longest_dragon','unique_queen_heads',
        'natural_food','own_recycled_food','early_splits_per_100_actions','late_splits_per_100_actions')},
        'queen_food_ledger_known_sides':sum(x['queen_food'] is not None for x in xs),
        **{k+'_total':sum(x[k] for x in xs if x[k] is not None) for k in ('splits','splits_at_length4','small_suicide_actions',
        'queen_food','queen_natural_food','queen_own_corpse_food','queen_own_recorded_suicide_food')}} for name,xs in teams.items()}
    out={'selection':read(ROOT/'selection.json'),'summary':{k:v for k,v in summary.items() if k not in ('matches','by_team')},
         'queen_death_reasons':deaths,'winner_already_led_at_round':{k:{'eligible_surviving_games':len(v),'led':sum(v)} for k,v in same_side_metrics.items()},
         'team_descriptions':by_team,'matches':games,
         'measurement_files':{str(p):sha(p) for p in [ROOT/'series-ui.json',ROOT/'resource-provenance.json',ROOT/'summary.json',
             *[Path('tools')/n for n in ('highrank_study.py','highrank_summary.py','highrank_resources.py','highrank_publish.py')]]},
         'notes':['Queen death reason A and recorded suicide are not proof of deliberate design or of a runtime error.',
                  'Old cached field verified_explicit_suicide_actions, where present, means verified recorded action type only.',
                  'Surviving-games snapshot denominator changes after elimination. Learning cohort is not validation.']}
    write(DOC/'oct7-highrank100-evidence.json',out)
    labels={'team_eliminated':'全队提前全灭','queen_dead':'Queen死亡，败于Queen项','queen_smaller_both_alive':'双方Queen存活，长度较短',
            'longest_peak_below_winner_final':'败于最长龙，历史峰值也不及胜方终值',
            'longest_capital_lost_or_reallocated':'败于最长龙，曾有足够峰值但未保留'}
    lines=['# 高分段100局逐场记录','',
      '固定20组、每组5局，17张地图、25队。双方均在取样时的2000分以上名单，取样完成后才解码回放。所有100局完整终局与平台胜者一致；99局通过严格食物/付费账，M1341270的空动作保持未知。',
      '', '下表是计分与轨迹分类，不是已证实的全部因果。Q为终局Queen长度，L为终局最长龙；数字均按左方A／右方B顺序。源码及比赛时对手版本未公开，不能由这些数字恢复其精确算法。', '',
      '| 对局 | 地图 | A / B | 胜方 | Q | L | 失败现象 |','|---|---|---|---|---:|---:|---|']
    for r in games:
        a,b=r['sides']['A'],r['sides']['B']
        lines.append(f"| [{r['match_id']}]({r['url']}) | {r['map'].lstrip('· ')} | {a['name']} / {b['name']} | {r['winner']} | {a['queen_length']}/{b['queen_length']} | {a['longest_dragon']}/{b['longest_dragon']} | {labels[r['loss_class']]} |")
    (DOC/'oct7-highrank100-matches.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'games':len(games),'teams':len(teams),'queen_death_reasons':deaths,'output':'docs/oct7-highrank100-evidence.json'}))

if __name__=='__main__':main()
