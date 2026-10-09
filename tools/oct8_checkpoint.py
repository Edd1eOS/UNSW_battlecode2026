"""Refresh the sprint's completed, frozen evidence inventory without counting aborted screens."""
import json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/oct8-sprint'
p=OUT/'checkpoint.json';checkpoint=json.loads(p.read_text(encoding='utf8'));panels=[]
excluded={'v181-v145-screen':'Aborted before the intended UTF-8 edit; not the corrected v181 screen or holdout.',
          'v221-no-queen-self-repulsion-screen':'Semantic duplicate: the parent already skipped Queen self-repulsion.'}
for summary in sorted(OUT.glob('*/summary.json')):
    directory=summary.parent;plan=directory/'plan.json'
    if not plan.exists() or directory.name in excluded:continue
    schedule=json.loads(plan.read_text());s=json.loads(summary.read_text())
    if 'candidate' not in schedule:continue
    games=list(directory.glob('games/*/result.json'))
    assert len(games)==s['games'],directory
    panels.append({'directory':directory.name,'candidate':schedule['candidate'],'opponents':schedule['plan']['opponents'],
                   'summary':s,'completed_games':len(games)})
online={};series=[]
for analysis in sorted(OUT.glob('v*/analysis.json')):
    data=json.loads(analysis.read_text());summary=data['summary'];series.append({'directory':analysis.parent.name,'summary':summary})
    for match in data['matches']:
        identity=match['match_id'];item={'match_id':identity,'version':summary['version'],'directory':analysis.parent.name,
                                      'raw_sha256':match['raw_sha256'],'ui_winner_consistent':match['ui_winner_consistent'],
                                      'gross_verified':match['gross_verified']}
        if identity in online:assert online[identity]['raw_sha256']==item['raw_sha256'],identity
        else:online[identity]=item
checkpoint.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),panels=panels,
                  excluded_panels=[{'directory':n,'reason':r} for n,r in excluded.items()],
                  completed_panel_count=len(panels),completed_panel_games=sum(x['completed_games'] for x in panels),
                  audited_online_games=len(online),online_series=series,online_matches=list(online.values()))
p.write_text(json.dumps(checkpoint,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({k:checkpoint[k] for k in ['completed_panel_count','completed_panel_games','audited_online_games','latest_confirmed_rating','active_platform_version']}))
