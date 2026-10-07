"""Full replay validation for one separately declared live probe."""
import argparse,json
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from highrank_study import one
from import_online_replays import scan_downloads,import_candidates

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ui',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--version',type=int,required=True);ap.add_argument('--expected-count',type=int,default=17);args=ap.parse_args()
    ui=json.loads(args.ui.read_text(encoding='utf8'));root=args.out;root.mkdir(exist_ok=True)
    if f'Your bot: v{args.version} ·' not in ui['main']:raise ValueError('Own version tag does not match frozen declaration')
    rows=[{'match_id':int(g['url'].split('/')[-1]),'series':ui['games'][0]['url'],'teams':ui['teams'],'our_team_id':1035,**g} for g in ui['games']]
    ids=[r['match_id'] for r in rows]
    if not 1<=args.expected_count<=17 or len(ids)!=args.expected_count or len(set(ids))!=args.expected_count:raise ValueError('Probe must retain every declared unique map')
    for sub in ('raw','reports'):(root/sub).mkdir(exist_ok=True)
    c,inventory,issues,ignored=scan_downloads(Path('D:/edge下载'),set(ids));imports=import_candidates(c,ids,root/'raw')
    if any(r['import_status']!='imported' for r in imports):raise ValueError('Incomplete/conflicting probe imports')
    (root/'imports.json').write_text(json.dumps(imports,indent=2),encoding='utf8')
    result=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(one,root,r) for r in rows]):result.append(f.result())
    own=next('AB'[i] for i,t in enumerate(ui['teams']) if t['url']=='/teams/1035')
    summary={'games':len(result),'version':args.version,'own_team':own,'outcomes':dict(Counter('win' if r['final']['leader']==own else 'draw' if r['final']['leader'] is None else 'loss' for r in result)),
             'complete':sum(r['quality']['complete_match_verified'] for r in result),'ui_agree':sum(r['ui_winner_consistent'] for r in result),'gross_verified':sum(r['gross_verified'] for r in result),
             'loss_axes':dict(Counter(r['final']['criterion'] for r in result if r['final']['leader']!=own)),
             'queen_survives':sum(r['final']['scores'][own]['queen_length']>0 for r in result),
             'mean_queen':sum(r['final']['scores'][own]['queen_length'] for r in result)/len(result),
             'mean_longest':sum(r['final']['scores'][own]['longest_dragon'] for r in result)/len(result),
             'splits':sum(r['resources'][own]['splits'] for r in result),
             'net_growth':sum(r['resources'][own]['recorded_update_net'] for r in result),
             'retained':sum(r['final']['scores'][own]['total_length'] for r in result)}
    (root/'analysis.json').write_text(json.dumps({'summary':summary,'matches':sorted(result,key=lambda r:r['match_id'])},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(summary))
if __name__=='__main__':main()
