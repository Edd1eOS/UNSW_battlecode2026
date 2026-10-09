"""Focused physical contracts for the Queen's four-step threat cache."""
from pathlib import Path
import argparse, importlib.util, json, re, shutil
from unswbc.sandbox import SandboxBot, WasmPool
from tools.verify_candidate import build

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('frames', ROOT/'external-benchmarks/smoke_external.py')
frame = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frame)

MAIN = r'''#include "helper.hpp"
#include "human.hpp"
int main(){auto [ct,game]=unswbc::init();strategy::Memory memory;
while(unswbc::update(ct,game)){
 memory.observe(ct);human::Map map(ct,memory);human::AttackCache cache(ct,memory,map);
 strategy::Simulation after{memory.body,{},(int)memory.body.size()==ct.get_length(),ct.get_length()};
 if(game.get_round_num()==201)after.eaten.push_back({5,4});
 auto risk=cache.assess(after);
 std::string note="CONTRACT certain="+std::to_string(risk.certain)+" potential="+std::to_string(risk.potential)+" paths="+std::to_string(cache.path_count);
 for(const auto& e:cache.enemies)note+=" enemy="+std::to_string(e.id)+",len="+std::to_string(e.minimum)+",complete="+std::to_string(e.complete);
 ct.set_indicator_string(note);ct.make_move(unswbc::Direction::SOUTH);unswbc::end_turn();
}}
'''

def run(candidate, out):
    source = out/'harness-source'
    source.mkdir(parents=True, exist_ok=True)
    for p in candidate.iterdir():
        if p.is_file() and p.suffix in ('.cpp','.h','.hpp','.toml'):
            shutil.copyfile(p,source/p.name)
    (source/'main.cpp').write_text(MAIN,encoding='utf-8')
    wasm,digest = build(source)
    queen=[(6,6),(7,6)]
    route=[(4,4),(5,4),(6,4),(6,5),(6,6)]
    base_edges=list(zip(route,route[1:]))+list(zip(queen,queen[1:]))
    short=[(4,4),(3,4)]
    three=[(4,4),(3,4),(3,3)]
    four=[(4,4),(3,4),(3,3),(4,3)]
    five=[(4,4),(4,3),(5,3),(6,3),(6,4)]
    cases=[
        ('complete-two-no-food-cannot-fund-four',short,(),(),200,(0,0)),
        ('complete-three-no-food-cannot-fund-four',three,(),(),200,(0,0)),
        ('complete-four-no-food-cannot-fund-four',four,(),(),200,(0,0)),
        ('previously-released-enemy-tail-is-legal',five,(),(),200,(1,0)),
        ('destination-pearl-cannot-fund-current-step',short,((5,4),(6,5)),(),200,(0,0)),
        ('three-earlier-pearls-fund-length2-four-step',short,((5,4),(6,4),(6,5)),(),200,(1,0)),
        ('queen-consumed-first-pearl-invalidates-chain',short,((5,4),(6,4),(6,5)),(),201,(0,0)),
        ('current-enemy-tail-still-solid',[(4,4),(4,3),(5,3),(5,4)],((5,4),(6,4),(6,5)),(),200,(0,0)),
        ('hidden-third-segment-is-potential-not-certain',[(4,4),(3,4),(2,4)],(),(),200,(0,1)),
    ]
    pool=WasmPool([str(wasm)],key='fourstep-contract-'+digest[:18]);rows=[]
    try:
        for name,body,pearls,extra,rnd,expected in cases:
            edges=base_edges+list(zip(body,body[1:]))+list(extra)
            # This partial enemy really continues beyond the observer window.
            # An open board keeps that boundary edge legal without fabricating
            # an unseen tile in the observed fixture.
            if name == 'hidden-third-segment-is-potential-not-certain':
                edges=None
            raw=frame.frame(0,queen,round_num=rnd,units=3,pearls=pearls,enemies=((18,body),),edges=edges)
            init='ID 0\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n'
            bot=SandboxBot(pool,init=init.encode(),name='contract-queen')
            try:
                output=bot.ask(raw.encode()).decode();match=re.search(r'certain=(\d+) potential=(\d+)',output)
                actual=tuple(map(int,match.groups())) if match else None
                rows.append(dict(name=name,expected=expected,actual=actual,passed=actual==expected and bot.error is None,
                                 output=output,error=bot.error,points=bot.live[0],input=init+raw))
            finally:bot.stop()
    finally:pool.close()
    report=dict(candidate=str(candidate),harness_source_sha256=digest,
                scope='Isolated attack-cache physical contracts. The emitted MOVE is a harness placeholder and not executed as a game. Round201 deliberately tests the Queen-consumed resource mask, not an empirical path claim.',rows=rows)
    (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('input','output')} for r in rows]))
    if not all(r['passed'] for r in rows):raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.candidate,a.out)
