"""Three-arm paired external experiment; no rating claims."""
import json,shutil,argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from verify_candidate import build
from night_external_panel import run_game,map_record,environment,write_json,digest,external_records
ROOT=Path(__file__).resolve().parents[1]
ARMS={'baseline':'v198-postmove-space','inheritance':'v254-inherited-capital-only','handoff':'v253-tail-capital-rescue','strict':'v255-confirmed-capital-handoff','delivery':'v256-local-capital-delivery'}
def task(args):return run_game(*args)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--maps',nargs='+',required=True);p.add_argument('--workers',type=int,default=3);p.add_argument('--arms',nargs='+',choices=ARMS,default=['baseline','inheritance','handoff']);a=p.parse_args()
 out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);external=external_records();env=environment();jobs=[];manifest={}
 for arm in a.arms:
  name=ARMS[arm]
  home=out/arm;(home/'candidate').mkdir(parents=True,exist_ok=True);(home/'maps').mkdir(exist_ok=True)
  wasm,h=build(ROOT/'opponents'/name);shutil.copyfile(wasm,home/'candidate/bot.wasm')
  frozen={'label':name,'source_bundle_sha256':h,'wasm_sha256':digest(Path(wasm).read_bytes())}
  maps={n:map_record(ROOT/'maps/current'/f'{n}.map') for n in a.maps}
  for n,x in maps.items():shutil.copyfile(x['source_path'],home/'maps'/f'{n}.map')
  plan={'maps':maps,'environment':env,'candidate_budget_margin_points':90000000,'opponents':external}
  schedule=[{'id':f'{opp}-{n}-{a.seed}-{side}','map':n,'seed':a.seed,'candidate_team':side,'opponent_team':'B' if side=='A' else 'A','opponent':opp} for n in a.maps for opp in external for side in 'AB']
  declaration={'plan':plan,'candidate':frozen,'jobs':schedule};write_json(home/'plan.json',declaration);manifest[arm]=declaration
  jobs += [(home,plan,frozen,j) for j in schedule if not (home/'games'/j['id']/'result.json').exists()]
 # Interleave arms so an interrupted run retains matched comparisons first.
 jobs.sort(key=lambda x:(x[3]['id'],x[0].name));write_json(out/'manifest.json',manifest)
 with ProcessPoolExecutor(max_workers=a.workers) as pool:
  for row in pool.map(task,jobs):print(json.dumps({'candidate':row['candidate']['label'],'game':row['id'],'outcome':row.get('official_outcome'),'peak':row['peak'][row['candidate_team']]['points'],'errors':row['invalid_runtime_events']}),flush=True)
 result={}
 for arm in a.arms:
  rows=[json.loads(p.read_text(encoding='utf8')) for p in (out/arm/'games').glob('*/result.json')]
  result[arm]={'games':len(rows),'outcomes':{o:sum(r.get('official_outcome')==o for r in rows) for o in ['win','loss','draw']},'candidate_errors':sum(r['invalid_runtime_events'][r['candidate_team']] for r in rows),'peak':max(r['peak'][r['candidate_team']]['points'] for r in rows)}
 write_json(out/'summary.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
