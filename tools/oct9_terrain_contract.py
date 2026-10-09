"""Focused terrain continuation contracts, not a strength evaluation."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil
from unswbc.sandbox import SandboxBot,WasmPool
from tools.verify_candidate import build
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frames',ROOT/'external-benchmarks/smoke_external.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
MAIN=r'''#include "helper.hpp"
#include "human.hpp"
int main(){auto [ct,game]=unswbc::init();strategy::Memory memory;
while(unswbc::update(ct,game)){memory.observe(ct);
 strategy::Simulation after{memory.body,{},(int)memory.body.size()==ct.get_length(),ct.get_length()};
 int budget=256;auto route=human::terrain_continuation(ct,memory,after,0,8,budget);
 ct.set_indicator_string("TERRAIN depth="+std::to_string(route.depth)+" uncertain="+std::to_string(route.uncertain)+" outside="+std::to_string(route.outside)+" nodes="+std::to_string(256-budget));
 ct.make_move(unswbc::Direction::SOUTH);unswbc::end_turn();}}
'''

def run(candidate,out):
    source=out/'harness-source';source.mkdir(parents=True,exist_ok=True)
    for p in candidate.iterdir():
        if p.is_file() and p.suffix in ('.cpp','.h','.hpp','.toml'):shutil.copyfile(p,source/p.name)
    (source/'main.cpp').write_text(MAIN,encoding='utf-8');wasm,digest=build(source)
    short=[(5,5),(4,5)];four=[(5,5),(4,5),(4,6),(5,6)]
    ring=[(5,5),(6,5),(6,6),(5,6),(4,6),(4,5),(5,5)]
    tight=[(5,5),(4,5),(4,6),(5,6),(5,5)]
    corridor=[(4,5),(5,5),(6,5),(7,5),(8,5)]
    cases=[
      ('dynamic-tail-follow-six-cell-ring',four,list(zip(ring,ring[1:])),(),False,(8,0)),
      ('current-tail-cannot-be-entered-before-removal',four,list(zip(tight,tight[1:])),(),False,(0,0)),
      ('known-dead-end-three-moves',short,list(zip(corridor,corridor[1:])),(),False,(3,0)),
      ('open-boundary-is-unknown-not-proven-dead',short,list(zip(corridor,corridor[1:])),(),True,(3,1)),
      ('movable-external-body-is-uncertain-not-fixed-wall',short,list(zip(corridor,corridor[1:])),((2,[(7,5),(8,5)]),),False,(1,1)),
    ]
    rows=[];pool=WasmPool([str(wasm)],key='terrain-contract-'+digest[:18])
    try:
      for name,body,edges,enemy,boundary,expected in cases:
        raw=f.frame(0,body,round_num=200,units=3,edges=edges,enemies=enemy)
        if boundary:
            lines=raw.splitlines();row=lines[-4].split();row[-1]='.';lines[-4]=' '.join(row);raw='\n'.join(lines)+'\n'
        init='ID 0\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n';bot=SandboxBot(pool,init=init.encode(),name=name)
        try:
            output=bot.ask(raw.encode()).decode();m=re.search(r'depth=(\d+) uncertain=(\d+)',output)
            actual=tuple(map(int,m.groups())) if m else None
            rows.append(dict(name=name,expected=expected,actual=actual,passed=actual==expected and bot.error is None,error=bot.error,points=bot.live[0],input=init+raw,output=output))
        finally:bot.stop()
    finally:pool.close()
    (out/'result.json').write_text(json.dumps({'scope':__doc__,'candidate':str(candidate),'harness_sha256':digest,'rows':rows},indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('input','output')} for r in rows]))
    if not all(r['passed'] for r in rows):raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.candidate,a.out)
