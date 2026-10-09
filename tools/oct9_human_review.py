"""Small physical-rule and transparent-choice probes, not a strength gate."""
from pathlib import Path
import argparse,importlib.util,json,re
from unswbc.sandbox import SandboxBot,WasmPool
from tools.verify_candidate import build
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frames',ROOT/'external-benchmarks/smoke_external.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def run(candidate,out):
    wasm,digest=build(candidate)
    head=(5,5);short=[head,(4,5)];long=[head,(4,5),(3,5),(2,5)]
    wall_path=[((5,5),(5,4)),((5,4),(6,4)),((6,4),(6,5)),((6,5),(7,5)),((7,5),(8,5)),((8,5),(8,4)),((8,4),(7,4))]
    queen_guard_edges=[((x,y),(x+dx,y+dy)) for x in range(3,10) for y in range(1,8) for dx,dy in ((1,0),(0,1)) if 3<=x+dx<10 and 1<=y+dy<8 and frozenset(((x,y),(x+dx,y+dy))) not in {frozenset(((5,5),(5,4))),frozenset(((5,5),(5,6)))}]
    scenarios=[
      ('queen-adjacent-food',0,short,dict(pearls=((6,5),)),['MOVE E'],'One immediately reachable uncontested pearl.'),
      ('worker-adjacent-food',2,short,dict(pearls=((6,5),)),['MOVE E'],'One immediately reachable uncontested pearl.'),
      ('long-worker-adjacent-safe-food',2,[(5,5),(4,5),(3,5),(2,5),(1,5),(0,5),(19,5),(18,5)],dict(round_num=200,units=3,pearls=((6,5),)),['MOVE E'],'Length8 scorer should still take an uncontested adjacent pearl; longer survival evaluation must not make it idle.'),
      ('worker-nearest-food',2,short,dict(pearls=((5,4),(7,5))),['MOVE N'],'North food1 away; east food2 away; both open.'),
      ('food-behind-wall-detour',2,short,dict(pearls=((6,5),),edges=wall_path),['MOVE N'],'Geometrically adjacent food requires3 steps; only legal first exit is north.'),
      ('toroidal-seam-food',2,[(0,5),(1,5)],dict(pearls=((19,5),)),['MOVE W'],'West seam is an ordinary wrapped edge.'),
      ('worker-guaranteed-queen-trade',2,long[:3],dict(units=3,enemies=((1,[(7,5),(8,5)]),)),['MOVE EE'],'Three-segment worker can pay second step to kill enemyQueen; both die.'),
      ('queen-partial-enemy-two-step-risk',0,[(5,6),(6,6),(6,7)],dict(units=3,enemies=((18,[(3,7),(2,7),(1,7)]),),pearls=((4,6),)),['MOVE N'],'Only two enemy segments visible, tail continues outsidewindow. Actual length3 can reach foodW viaNE; queen should leaveN.'),
      ('queen-complete-length2-no-phantom-sprint',0,[(5,6),(6,6),(6,7)],dict(units=3,enemies=((18,[(3,7),(3,8)]),),pearls=((4,6),)),['MOVE W'],'Complete visible enemy length2 cannot pay second step ontofood; Queen may safely take immediateW pearl.'),
      ('queen-visible-two-step-ambush',0,[(5,6),(6,6),(6,7)],dict(units=3,enemies=((18,[(3,7),(3,8),(3,9)]),),pearls=((3,6),)),['MOVE N'],'West approaches food but lets fully visible length3 enemy execute NE and kill Queen; north escapes its two-step reach.'),
      ('worker-must-not-close-queen-sole-exit',2,[(6,4),(7,4)],dict(units=3,allies=((0,[(5,5),(4,5)]),),pearls=((6,5),),edges=queen_guard_edges),None,'FoodS occupies the only current Queen outlet; prefer a different legal move.'),
      ('split-two-distinct-exits-but-no-room',2,[(5,5),(4,5),(4,6),(5,6)],dict(units=3,edges=[((5,5),(6,5)),((6,5),(6,6)),((6,6),(5,6))]),['MOVE E'],'Six-cell ring: four-body can survive nonsplit; split gives distinct outlets but creates two mutually trapping two-body units. Many empty tiles behind walls are irrelevant.'),
      ('split-shared-sole-exit-trap',2,[(5,5),(4,5),(4,6),(5,6),(6,6)],dict(units=3,edges=[((5,5),(6,5)),((6,6),(6,5))]),['MOVE E'],'Splitting leaves parent and child competing for same sole tile; moving keeps a legal six-cell ring.'),
      ('length2-cannot-afford-two-step-trade',2,short,dict(units=3,enemies=((1,[(7,5),(8,5)]),)),None,'Do not emit EE: length2 cannot pay second step; expectation is legality, not strategy.'),
    ]
    pool=WasmPool([str(wasm)],key='oct9-human-'+digest[:24]);rows=[]
    try:
      for name,identity,body,kwargs,expected,reason in scenarios:
        kwargs=dict(kwargs);allies=kwargs.pop('allies',())
        if allies:kwargs['enemies']=(*kwargs.get('enemies',()),*allies)
        raw=f.frame(identity,body,round_num=kwargs.pop('round_num',10),**kwargs)
        for aid,_ in allies:raw=raw.replace('B '+str(aid)+' ','A '+str(aid)+' ')
        init=f'ID {identity}\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n'
        bot=SandboxBot(pool,init=init.encode(),name=str(identity))
        try:
          output=bot.ask(raw.encode()).decode('utf-8','replace')
          actions=re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$',output,re.M)
          points,mem=bot.live
          passed=not bot.error and len(actions)==1 and points<90000000
          agreement=actions==expected if expected is not None else actions!=['MOVE S'] if name=='worker-must-not-close-queen-sole-exit' else actions!=['MOVE EE']
          rows.append(dict(name=name,reason=reason,input=init+raw,output=output,actions=actions,expected=expected,human_agreement=agreement,protocol_pass=passed,cpu_points=points,error=bot.error))
        finally:bot.stop()
    finally:pool.close()
    report=dict(candidate=str(candidate),source_bundle_sha256=digest,scope=f'{len(scenarios)} isolated observations; no matches, no strength inference, no upload veto',rows=rows)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps([dict(name=r['name'],actions=r['actions'],agreement=r['human_agreement'],protocol=r['protocol_pass'],points=r['cpu_points']) for r in rows]))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.candidate,a.out)
