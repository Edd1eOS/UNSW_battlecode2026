"""Paired Oct8 regression against frozen versions; official engine and restart audit."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import json
import shutil
from verify_candidate import build
from night_external_panel import run_game, map_record, environment, write_json, digest

ROOT = Path(__file__).resolve().parents[1]

def task(args):
    return run_game(*args)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',required=True)
    p.add_argument('--opponent',default='opponents/v114-evaluation-cache')
    p.add_argument('--out',required=True)
    p.add_argument('--maps',nargs='+',default=['australia','default','maze','portals','unsw','weakhold'])
    p.add_argument('--seed',type=int,default=2026100801)
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args(); out=ROOT/a.out
    out.mkdir(parents=True,exist_ok=True)
    cw,ch=build(ROOT/a.candidate); ow,oh=build(ROOT/a.opponent)
    for sub,wasm in [('candidate',cw),('opponent',ow)]:
        (out/sub).mkdir(exist_ok=True); shutil.copyfile(wasm,out/sub/'bot.wasm')
    maps={n:map_record(ROOT/'maps/current'/f'{n}.map') for n in a.maps}
    (out/'maps').mkdir(exist_ok=True)
    for n in maps: shutil.copyfile(maps[n]['source_path'],out/'maps'/f'{n}.map')
    frozen={'label':Path(a.candidate).name,'source_bundle_sha256':ch,'wasm_sha256':digest(Path(cw).read_bytes())}
    plan={'maps':maps,'environment':environment(),'candidate_budget_margin_points':90000000,
          'opponents':{Path(a.opponent).name:{'path':str((out/'opponent').resolve()),'source_bundle_sha256':oh}}}
    jobs=[{'id':f'{n}-{a.seed}-{s}','map':n,'seed':a.seed,'candidate_team':s,
           'opponent_team':'B' if s=='A' else 'A','opponent':Path(a.opponent).name} for n in a.maps for s in 'AB']
    declaration={'plan':plan,'candidate':frozen,'jobs':jobs}
    if (out/'plan.json').exists() and json.loads((out/'plan.json').read_text())!=declaration:
        raise ValueError('Existing panel has a different source, environment or schedule; use a fresh output directory')
    write_json(out/'plan.json',declaration)
    pending=[j for j in jobs if not (out/'games'/j['id']/'result.json').exists()]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for row in pool.map(task,[(out,plan,frozen,j) for j in pending]):
            print(json.dumps({'game':row['id'],'outcome':row.get('official_outcome'),
                              'queen':row.get('engine_result'), 'peak':row['peak'][row['candidate_team']]['points'],
                              'errors':row['invalid_runtime_events']}),flush=True)
    rows=[json.loads((out/'games'/j['id']/'result.json').read_text()) for j in jobs]
    result={'games':len(rows),'outcomes':{o:sum(r.get('official_outcome')==o for r in rows) for o in ['win','loss','draw']},
            'candidate_peak':max(r['peak'][r['candidate_team']]['points'] for r in rows),
            'candidate_errors':sum(r['invalid_runtime_events'][r['candidate_team']] for r in rows),
            'opponent_errors':sum(r['invalid_runtime_events'][r['opponent_team']] for r in rows)}
    write_json(out/'summary.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
