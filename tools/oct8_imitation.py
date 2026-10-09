"""Learn a small movement ranking model from legal-window public expert actions.

No opponent code, hidden-map feature, or hidden enemy body is used. Portal edges
are excluded from these local features. Split actions are excluded, not relabelled.
Holdout groups are entire replays/maps, never random turns from the same game.
"""
import argparse,json,hashlib
from pathlib import Path
from collections import deque,Counter
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from audit_online import load_replay
from oct7_exploration_death_audit import Board,point

NAMES=['eat','space','food_near','food_sum','food_count','exit_degree','frontier_near',
       'enemy_head_near','enemy_body_near','ally_head_near','queen_near','recent','straight','spawn_near','dead_end']

def features(board,live,pearls,timers,history,who,facing,rnd):
 v=live[who];head=v['body'][0];body=v['body'];team=v['team']
 window={((head[0]+dx)%board.W,(head[1]+dy)%board.H) for dy in range(-3,4) for dx in range(-3,4)}
 parts={p:(i,x['team'],j==0) for i,x in live.items() for j,p in enumerate(x['body']) if p in window}
 adj={p:[] for p in window};frontier=set()
 for p in window:
  for d in 'NESW':
   if board.edges.get(board.edge(p,d),(0,0))[0]!=0:continue
   n=board.step(p,d)
   if n in window:adj[p].append(n)
   else:frontier.add(p)
 heads=[(p,t,i) for p,(i,t,h) in parts.items() if h and i!=who]
 def metric(a,b):
  dx=abs(a[0]-b[0]);dy=abs(a[1]-b[1]);return min(dx,board.W-dx)+min(dy,board.H-dy)
 X=np.zeros((4,len(NAMES)*3),np.float32);valid=np.zeros(4,bool)
 for k,d in enumerate('NESW'):
  if board.edges.get(board.edge(head,d),(0,0))[0]!=0:continue
  n=board.step(head,d)
  if n not in window or n in parts:continue
  valid[k]=True;occupied=set(parts)
  if n not in pearls:occupied.discard(body[-1])
  dist={n:0};q=deque([n])
  while q:
   p=q.popleft()
   for z in adj[p]:
    if z in occupied or z in dist:continue
    dist[z]=dist[p]+1;q.append(z)
  fd=[depth for p,depth in dist.items() if p in pearls]
  sd=[depth+max(0,timers[p]) for p,depth in dist.items() if timers.get(p,-1)>=0]
  enemyheads=[metric(n,p) for p,t,i in heads if t!=team]
  enemybody=[metric(n,p) for p,(i,t,h) in parts.items() if t!=team]
  allyheads=[metric(n,p) for p,t,i in heads if t==team]
  queen=[metric(n,p) for p,t,i in heads if t==team and i<2]
  fr=[dist[p] for p in frontier if p in dist]
  degree=sum(z not in occupied for z in adj[n])
  inv=lambda a:1/(1+min(a)) if a else 0
  f=np.array([float(n in pearls),len(dist)/49,inv(fd),sum(1/(1+z) for z in fd)/5,len(fd)/10,
    degree/4,inv(fr),inv(enemyheads),inv(enemybody),inv(allyheads),inv(queen),
    sum(p==n for p in history.get(who,()))/4,float(d==facing.get(who)),inv(sd),float(degree==0)],np.float32)
  X[k]=np.concatenate([f,f*min(len(body),16)/16,f*rnd/500])
 return X,valid

def extract(task):
 path,team,limit=task;r=load_replay(Path(path),node_path='D:/node/node.exe');board=Board(r['map'])
 live={x['id']:{'team':x['team'],'body':list(map(point,x['body']))} for x in r['initial_dragons']}
 facing={};history={};pearls=set();timers={};rnd=0;xs=[];ys=[];ms=[];stats=Counter()
 # Replay countdown values are the same public values seen on visible tiles.
 for e in r['events']:
  t=e['type']
  if t=='roundStart':rnd=e['round'];timers={p:n-1 for p,n in timers.items()}
  elif t=='tileChange':
   p=point(e['tile']);pearls.add(p) if e['hasPearl'] else pearls.discard(p)
  elif t=='pearlCountdown':timers[point(e['tile'])]=e['countdown']
  elif t=='turnStart':
   i=e['id'];history.setdefault(i,deque(maxlen=24)).append(live[i]['body'][0])
  elif t=='dragonAction':
   i=e['id'];a=e['action'];v=live[i]
   if i<=1 or v['team']!=team:continue
   stats[a['kind']]+=1
   if a['kind']!='move' or len(a['steps'])!=1 or len(xs)>=limit:continue
   # Deterministic thinning covers the entire match instead of its opening only.
   if (i*17+rnd*7)%3:continue
   X,valid=features(board,live,pearls,timers,history,i,facing,rnd);y='NESW'.index(a['steps'][0])
   if valid.sum()<2 or not valid[y]:stats['excluded_choice']+=1;continue
   xs.append(X);ys.append(y);ms.append(valid)
  elif t=='dragonUpdate':
   i=e['id'];v=live[i];v['body'].insert(0,point(e['head']));tail=point(e['tail']);facing[i]=e['facing']
   while len(v['body'])>1 and v['body'][-1]!=tail:v['body'].pop()
  elif t=='dragonSplit':
   live[e['parentId']]['body']=list(map(point,e['parentBody']))
   live[e['childId']]={'team':e['team'],'body':list(map(point,e['childBody']))};facing[e['childId']]=e['childFacing']
  elif t=='dragonDeath':live.pop(e['id'],None)
 return np.array(xs),np.array(ys),np.array(ms),{'path':path,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'examples':len(xs),'actions':dict(stats)}

def train(root,out):
 files=sorted(root.glob('*.replay'));out.mkdir(parents=True,exist_ok=True)
 with ProcessPoolExecutor(max_workers=2) as pool:
  results=list(pool.map(extract,[(str(p),'B',4000) for p in files]))
 x=np.concatenate([r[0] for r in results]);y=np.concatenate([r[1] for r in results]);mask=np.concatenate([r[2] for r in results])
 groups=np.concatenate([np.full(len(r[1]),i) for i,r in enumerate(results)])
 held=groups%4==0;trainmask=~held
 w=np.zeros(x.shape[-1],np.float64);m=w.copy();v=w.copy();rng=np.random.default_rng(20261008)
 tx,ty,tm=x[trainmask],y[trainmask],mask[trainmask]
 for step in range(1,2501):
  ids=rng.integers(len(tx),size=512);bx,by,bm=tx[ids],ty[ids],tm[ids]
  z=np.einsum('bdf,f->bd',bx,w);z[~bm]=-1e6;z-=z.max(axis=1)[:,None]
  p=np.exp(z);p/=p.sum(axis=1)[:,None];p[np.arange(len(ids)),by]-=1
  g=np.einsum('bd,bdf->f',p,bx)/len(ids)+0.0003*w
  m=.9*m+.1*g;v=.999*v+.001*g*g;w-=.025*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8)
 def metrics(sel):
  z=np.einsum('bdf,f->bd',x[sel],w);z[~mask[sel]]=-1e6
  return {'examples':int(sel.sum()),'top1_accuracy':float((z.argmax(axis=1)==y[sel]).mean())}
 report={'features':NAMES,'interactions':['base','length_capped16/16','round/500'],'weights':w.tolist(),
         'training':metrics(trainmask),'heldout_maps':metrics(held),'replays':[r[3] for r in results]}
 (out/'model.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 np.savez_compressed(out/'dataset.npz',x=x,y=y,mask=mask,groups=groups)
 print(json.dumps({k:v for k,v in report.items() if k not in ('weights','replays')}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();train(a.root,a.out)
