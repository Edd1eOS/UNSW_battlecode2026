"""Cold reconstruction of V5 Portals legal own observation packets.

Reads an official replay only. It never compiles/runs a bot or engine match,
loads strategy caches, or exposes hidden fields in the generated packets.
This fixture source assumes the verified V5/SAS game has no own sonar/inbox.
"""
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_online import load_replay
DIRS='NESW'; DELTA={'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}
def point(p):return(p['x'],p['y'])
class Board:
 def __init__(self,text):
  self.edges={}; self.portals={}
  for line in text.splitlines():
   a=line.split()
   if not a:continue
   if a[0]=='MAP':self.W,self.H=map(int,a[1:])
   elif a[0]=='EDGE':
    idx,kind,pid=map(int,a[1:]); x=idx%(self.W+1);row=idx//(self.W+1)
    if x>=self.W or row>=2*self.H:continue
    e=('H' if row%2==0 else 'V',x,row//2);self.edges[e]=(kind,pid)
    if kind==2:self.portals.setdefault(pid,[]).append(e)
 def edge(self,p,d):
  x,y=p
  return {'N':('H',x,y),'S':('H',x,(y+1)%self.H),'W':('V',x,y),'E':('V',(x+1)%self.W,y)}[d]
 def step(self,p,d):
  e=self.edge(p,d);kind,pid=self.edges.get(e,(0,0))
  if kind==1:return None
  if kind==2:
   ports=self.portals[pid];other=next(q for q in ports if q!=e);o,x,y=other
   return ((x-(d=='W'))%self.W,(y-(d=='N'))%self.H)
  dx,dy=DELTA[d];return((p[0]+dx)%self.W,(p[1]+dy)%self.H)
 def visible(self,p,c):return min((p[0]-c[0])%self.W,(c[0]-p[0])%self.W)<=3 and min((p[1]-c[1])%self.H,(c[1]-p[1])%self.H)<=3


def initial_countdowns(map_text):
    result = {}
    for line in map_text.splitlines():
        fields = line.split()
        if fields and fields[0] == "TILE":
            minimum, maximum = map(int, fields[3:5])
            if minimum < 0 or maximum < 0 or (maximum > 0 and not 1 <= minimum <= maximum):
                raise ValueError("Invalid official TILE respawn bounds")
            # config.cc: mSpawnsPearls is maxGap > 0, regardless of minGap.
            if maximum > 0:
                result[(int(fields[1]), int(fields[2]))] = 0
    return result


def assert_no_sonar(replay):
    # This narrow exporter intentionally refuses streams requiring inbox/echo
    # reconstruction instead of silently supplying empty fields.
    if any(event["type"] == "sonarPing" for event in replay["events"]):
        raise ValueError("Sonar replay needs explicit inbox/echo reconstruction")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,default=ROOT/'test-results/external-panel-v5-20261006/games/holdout/sas-987/portals-2026100695-B/raw.replay')
    parser.add_argument('--out-dir',type=Path,default=ROOT/'test-results/exploration-ro')
    parser.add_argument('--ids',type=int,nargs='+',default=[1,3,5])
    parser.add_argument('--node',default=r'D:\node\node.exe')
    args=parser.parse_args(argv);args.out_dir.mkdir(parents=True,exist_ok=True)
    r=load_replay(args.replay,node_path=args.node)
    assert_no_sonar(r)
    initial_teams={v['id']:v['team'] for v in r['initial_dragons']}
    if not all(who in initial_teams for who in args.ids):raise ValueError('This cold fixture exporter selects initial dragon IDs only')
    b=Board(r['map']);live={v['id']:{'team':v['team'],'body':list(map(point,v['body'])),'facing':None} for v in r['initial_dragons']};pearls=set();countdowns={};roundno=None;frames={who:[] for who in args.ids};records={who:[] for who in frames}
    countdowns=initial_countdowns(r['map'])
    for e in r['events']:
     t=e['type']
     if t=='tileChange':p=point(e['tile']);pearls.add(p) if e['hasPearl'] else pearls.discard(p)
     elif t=='pearlCountdown':countdowns[point(e['tile'])]=e['countdown']
     elif t=='roundStart':
      roundno=e['round']
      # PearlTick decrements every bed each round; only resets emit countdown events.
      countdowns={p:n-1 for p,n in countdowns.items()}
     elif roundno is None:continue
     elif t=='turnStart' and e['id'] in frames:
      who=e['id'];v=live[who];head=v['body'][0];window=[((head[0]+dx)%b.W,(head[1]+dy)%b.H) for dy in range(-3,4) for dx in range(-3,4)]
      facing=v['facing'] or next(d for d in DIRS if b.step(v['body'][1],d)==head)
      lines=[f'ROUND {roundno}','DIR '+facing,'LENGTH '+str(len(v['body'])),'UNIT_COUNT '+str(sum(vv['team']==v['team'] for vv in live.values())),'NUM_MSGS 0','ECHOES 0 0 0 0 0']
      lines += [f'{p[0]} {p[1]} {int(p in pearls)} {countdowns.get(p,-1)}' for p in window]
      parts=[]
      for other,vv in live.items():
       for i,p in enumerate(vv['body']):
        if not b.visible(p,head):continue
        facingPart=(vv['facing'] or next(d for d in DIRS if b.step(vv['body'][1],d)==p)) if i==0 else next(d for d in DIRS if b.step(p,d)==vv['body'][i-1])
        parts.append(f'{vv["team"]} {other} {p[0]} {p[1]} {facingPart} {int(i==0)}')
      lines += ['DRAGON_BODIES '+str(len(parts)),*parts]
      def edgeval(edge):
       kind,pid=b.edges.get(edge,(0,0));return '.' if kind==0 else 'w' if kind==1 else str(pid)
      for dy in range(-3,5):lines.append(' '.join(edgeval(('H',(head[0]+dx)%b.W,(head[1]+dy)%b.H)) for dx in range(-3,4)))
      for dy in range(-3,4):lines.append(' '.join(edgeval(('V',(head[0]+dx)%b.W,(head[1]+dy)%b.H)) for dx in range(-3,5)))
      frames[who].append('\n'.join(lines)+'\n');records[who].append({'round':roundno,'body':v['body'].copy(),'head':head})
     elif t=='dragonAction' and e['id'] in records and records[e['id']]:records[e['id']][-1]['action']=e['action']
     elif t=='dragonUpdate':
      v=live[e['id']];v['body'].insert(0,point(e['head']));tail=point(e['tail']);v['facing']=e['facing']
      while len(v['body'])>1 and v['body'][-1]!=tail:v['body'].pop()
     elif t=='dragonSplit':
      live[e['parentId']]['body']=list(map(point,e['parentBody']));live[e['childId']]={'team':e['team'],'body':list(map(point,e['childBody'])),'facing':e['childFacing']}
     elif t=='dragonDeath':del live[e['id']]
    for who,rows in frames.items():
     inp=f'ID {who}\nTEAM {initial_teams[who]}\nMAP {b.W} {b.H}\nUNIT_LIMIT 64\n'+''.join(rows)+'ENDGAME\n'
     (args.out_dir/f'v5-portals-unit{who}-input.json').write_text(json.dumps({'input':inp,'frames':len(rows),'source':'Full500turn continuous legal observations reconstructed from frozen V5 executed replay; no invented memory; no matches','source_replay_sha256':r['input_sha256'],'recorded_actions':records[who]},indent=2))
     print('unit',who,'frames',len(rows),'headcount',len(set(tuple(t['head']) for t in records[who])),'last50',sorted({tuple(t['head']) for t in records[who][-50:]}))


if __name__ == "__main__":
    main()
