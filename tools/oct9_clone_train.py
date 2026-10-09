"""Learn legal-window macro decisions and movement ranks from selected public teachers."""
import json,hashlib
from pathlib import Path
from collections import Counter,deque
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from audit_online import load_replay
from oct7_exploration_death_audit import Board,point
from oct8_imitation import features
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/oct9-imitation'
NAMES=['queen','length','round','units','enemy_heads','ally_heads','queen_distance','larger_heads','max_ally_visible_length','free_neighbours','adjacent_food','visible_food','tail_visible','tail_free','enemy_distance','walls']
def extract(job):
 d=load_replay(Path(job['path']),node_path='D:/node/node.exe');board=Board(d['map']);live={v['id']:{'team':v['team'],'body':list(map(point,v['body']))} for v in d['initial_dragons']};pearls=set();timers={};history={};facing={};rnd=0;mx=[];my=[];mw=[];xx=[];yy=[];vv=[];qq=[];counts=Counter()
 for e in d['events']:
  k=e['type']
  if k=='roundStart':rnd=e['round'];timers={p:n-1 for p,n in timers.items()}
  elif k=='tileChange':
   p=point(e['tile']);pearls.add(p) if e['hasPearl'] else pearls.discard(p)
  elif k=='pearlCountdown':timers[point(e['tile'])]=e['countdown']
  elif k=='turnStart':history.setdefault(e['id'],deque(maxlen=24)).append(live[e['id']]['body'][0])
  elif k=='dragonAction':
   i=e['id'];a=e.get('action');v=live[i]
   if v['team']!=job['team'] or not a:continue
   body=v['body'];head=body[0];length=len(body);kind=a['kind'];label=0
   if kind=='suicide':label=4
   elif kind=='split':
    child=a['childSegmentCount'];label=4 if child<2 else 1 if child==2 else 3 if child==length-2 else 2
   if kind=='move' and len(a['steps'])==1 and board.step(head,a['steps'][0]) in body[1:]:label=4
   counts[str(label)]+=1
   if label==0 and (i*17+rnd*7)%5:continue
   window={((head[0]+dx)%board.W,(head[1]+dy)%board.H) for dy in range(-3,4) for dx in range(-3,4)}
   parts={p:(j,z['team'],n==0) for j,z in live.items() for n,p in enumerate(z['body']) if p in window}
   def dist(p):
    dx=abs(p[0]-head[0]);dy=abs(p[1]-head[1]);return min(dx,board.W-dx)+min(dy,board.H-dy)
   enemies=[p for p,(j,t,h) in parts.items() if h and t!=v['team']];allies=[(p,j) for p,(j,t,h) in parts.items() if h and t==v['team'] and j!=i];size=Counter(j for j,t,h in parts.values());queens=[dist(p) for p,j in allies if j<=1]
   free=[p for dd in 'NESW' if (p:=board.step(head,dd)) is not None and p in window and p not in parts]
   tail=body[-1];tailfree=sum((p:=board.step(tail,dd)) is not None and p in window and p not in parts for dd in 'NESW') if tail in window else 0
   f=[i<=1,length,rnd,sum(z['team']==v['team'] for z in live.values()),len(enemies),len(allies),min(queens,default=99),sum(size[j]>length for p,j in allies),max((size[j] for p,j in allies),default=0),len(free),sum(p in pearls for p in free),len(pearls&window),tail in window,tailfree,min((dist(p) for p in enemies),default=99),sum(board.step(head,dd) is None for dd in 'NESW')]
   mx.append(f);my.append(label);mw.append(5 if label==0 else 1)
   if kind=='move' and label==0 and a['steps'] and (i*3+rnd)%3==0 and len(xx)<1800:
    X,valid=features(board,live,pearls,timers,history,i,facing,rnd);y='NESW'.index(a['steps'][0])
    if valid.sum()>=2 and valid[y]:xx.append(X);yy.append(y);vv.append(valid);qq.append(i<=1)
  elif k=='dragonUpdate':
   v=live[e['id']];v['body'].insert(0,point(e['head']));tail=point(e['tail']);facing[e['id']]=e['facing']
   while len(v['body'])>1 and v['body'][-1]!=tail:v['body'].pop()
  elif k=='dragonSplit':
   live[e['parentId']]['body']=list(map(point,e['parentBody']));live[e['childId']]={'team':e['team'],'body':list(map(point,e['childBody']))};facing[e['childId']]=e['childFacing']
  elif k=='dragonDeath':live.pop(e['id'],None)
 return (np.array(mx,np.float32),np.array(my),np.array(mw,np.float32),np.array(xx,np.float32).reshape(-1,4,45),np.array(yy,dtype=int),np.array(vv,dtype=bool).reshape(-1,4),np.array(qq,dtype=bool),{**job,'sha256':d['input_sha256'],'action_counts':dict(counts)})
def treefit(X,y,w,depth=7):
 nodes=[]
 def rec(ids,level):
  idx=len(nodes);cnt=np.bincount(y[ids],weights=w[ids],minlength=5);prob=cnt/cnt.sum();nodes.append({'f':-1,'v':0,'l':-1,'r':-1,'p':prob.tolist()})
  if level==depth or len(ids)<140 or prob.max()>.998:return idx
  best=None
  for j in range(X.shape[1]):
   vals=np.unique(np.quantile(X[ids,j],np.linspace(.04,.96,18)))
   for v in vals:
    mask=X[ids,j]<=v;nl=int(mask.sum())
    if nl<60 or nl>len(ids)-60:continue
    c=np.bincount(y[ids[mask]],weights=w[ids[mask]],minlength=5);other=cnt-c
    score=(c@c)/c.sum()+(other@other)/other.sum()
    if best is None or score>best[0]:best=(score,j,float(v),mask)
  if best is not None:
   _,j,v,m=best;nodes[idx].update(f=j,v=v,l=rec(ids[m],level+1),r=rec(ids[~m],level+1))
  return idx
 rec(np.arange(len(y)),0);return nodes
def predict(nodes,x):
 pred=[]
 for row in x:
  n=nodes[0]
  while n['f']>=0:n=nodes[n['l'] if row[n['f']]<=n['v'] else n['r']]
  pred.append(np.argmax(n['p']))
 return np.array(pred)
def main():
 jobs=json.loads((OUT/'selection.json').read_text());cache=OUT/'datasets';cache.mkdir(exist_ok=True);results=[]
 with ProcessPoolExecutor(max_workers=3) as pool:
  for r in pool.map(extract,jobs):results.append(r);print('extracted',r[-1]['match'],r[-1]['teacher'],len(r[0]),len(r[3]),flush=True)
 X,y,w=[np.concatenate([r[i] for r in results]) for i in range(3)];groups=np.concatenate([np.full(len(r[0]),r[-1]['match']) for r in results]);held=groups%5==0
 nodes=treefit(X[~held],y[~held],w[~held]);pred=predict(nodes,X[held]);metrics={'macro_heldout_samples':int(held.sum()),'macro_weighted_accuracy':float(np.average(pred==y[held],weights=w[held])),'per_class':{str(k):{'n':int(sum(y[held]==k)),'recall':float(np.mean(pred[y[held]==k]==k)) if sum(y[held]==k) else None} for k in range(5)}}
 XX,yy,mask,queen=[np.concatenate([r[i] for r in results]) for i in range(3,7)];mg=np.concatenate([np.full(len(r[3]),r[-1]['match']) for r in results]);weights=[]
 for role in [False,True]:
  sel=(queen==role)&(mg%5!=0);tx,ty,tm=XX[sel],yy[sel],mask[sel];ww=np.zeros(45);m=ww.copy();v=ww.copy();rng=np.random.default_rng(90210)
  for step in range(1,1001):
   ids=rng.integers(len(tx),size=512);bx,by,bm=tx[ids],ty[ids],tm[ids];z=np.einsum('bdf,f->bd',bx,ww);z[~bm]=-1e6;z-=z.max(axis=1)[:,None];pp=np.exp(z);pp/=pp.sum(axis=1)[:,None];pp[np.arange(len(ids)),by]-=1;g=np.einsum('bd,bdf->f',pp,bx)/len(ids)+.0003*ww;m=.9*m+.1*g;v=.999*v+.001*g*g;ww-=.025*m/(1-.9**step)/(np.sqrt(v/(1-.999**step))+1e-8)
  weights.append(ww.tolist());ss=(queen==role)&(mg%5==0);z=np.einsum('bdf,f->bd',XX[ss],ww);z[~mask[ss]]=-1e6;metrics['movement_'+str(role)]={'train':int(sel.sum()),'held':int(ss.sum()),'accuracy':float(np.mean(z.argmax(axis=1)==yy[ss]))}
 report={'features':NAMES,'actions':['move','split2','split_half','tail_handoff','donate'],'metrics':metrics,'nodes':nodes,'movement_weights':weights,'sources':[r[-1] for r in results],'scope':'Behavior cloning from public partial-observation traces, not private algorithm recovery or strength proof.'};(OUT/'model.json').write_text(json.dumps(report,indent=2));np.savez_compressed(cache/'macro.npz',X=X,y=y,w=w,groups=groups)
 target=ROOT/'opponents/v257-topnine-clone';target.mkdir(exist_ok=True)
 h='#pragma once\nnamespace topclone {\nstruct Node {int f;double v;int l,r;double p[5];};\ninline constexpr Node NODES[]={\n'
 for n in nodes:h+='{'+f"{n['f']},{n['v']:.10g},{n['l']},{n['r']},"+'{'+','.join(f'{p:.10g}' for p in n['p'])+'}},\n'
 h+='};\ninline constexpr double MOVE_WEIGHTS[2][45]={'+','.join('{'+','.join(f'{v:.10g}' for v in a)+'}' for a in weights)+'};\n}\n';(target/'clone_weights.hpp').write_text(h)
 print(json.dumps(metrics),flush=True)
if __name__=='__main__':main()
