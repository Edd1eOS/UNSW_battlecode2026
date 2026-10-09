"""Visible static-occupancy continuation analysis of v270 Islands round42.

Not a synthesized bot input or a match: future actors are frozen, the Queen's
actual own body moves exactly, and no tile outside the current window is used.
"""
from pathlib import Path
import json
from tools.audit_online import load_replay
from tools.oct7_exploration_death_audit import Board,point

def main():
    path=Path('test-results/oct9-last30/online-v270-manny/M1533763.replay')
    d=load_replay(path,node_path='D:/node/node.exe');b=Board(d['map']);pearls=set();rnd=-1
    live={v['id']:{'team':v['team'],'body':list(map(point,v['body']))} for v in d['initial_dragons']}
    for e in d['events']:
        k=e['type']
        if k=='tileChange':
            p=point(e['tile']);pearls.add(p) if e['hasPearl'] else pearls.discard(p)
        elif k=='roundStart':rnd=e['round']
        elif k=='turnStart' and e['id']==1 and rnd==42:break
        elif k=='dragonUpdate' and rnd>=0:
            body=live[e['id']]['body'];body.insert(0,point(e['head']));tail=point(e['tail'])
            while len(body)>1 and body[-1]!=tail:body.pop()
        elif k=='dragonSplit':
            live[e['parentId']]['body']=list(map(point,e['parentBody']))
            live[e['childId']]={'team':e['team'],'body':list(map(point,e['childBody']))}
        elif k=='dragonDeath':del live[e['id']]
    queen=live[1]['body'];head=queen[0]
    visible={(x,y) for x in range(b.W) for y in range(b.H) if b.visible((x,y),head)}
    occupied={p for i,v in live.items() if i!=1 for p in v['body'] if p in visible}
    initial_food=pearls & visible
    def step(body,food,direction):
        p=b.step(body[0],direction)
        if p is None or p not in visible or p in body or p in occupied:return None
        newer=[p]+body;food=set(food)
        if p in food:food.remove(p)
        else:newer.pop()
        return newer,food
    rows=[]
    for action in ['N','E','S','W','SSE']:
        body=list(queen);food=set(initial_food);valid=True
        for direction in action:
            answer=step(body,food,direction)
            if answer is None:valid=False;break
            body,food=answer
        row={'action':action,'legal':valid}
        if valid:
            best=[''];nodes=[0];frontiers=[]
            def dfs(body,food,path):
                nodes[0]+=1
                if len(path)>len(best[0]):best[0]=path
                if len(path)>=12:return True
                if nodes[0]>=100000:return False
                for direction in 'NESW':
                    target=b.step(body[0],direction)
                    if target is not None and target not in visible:
                        # Only the boundary edge is observed. The destination
                        # occupancy and continuation remain explicitly unknown.
                        frontiers.append({'path':path+direction,'unobserved_destination':target})
                    nxt=step(body,food,direction)
                    if nxt and dfs(*nxt,path+direction):return True
                return False
            found=dfs(body,food,'')
            row.update(after_body=body,max_proven_visible_continuation=len(best[0]),continuation=best[0],found_twelve=found,nodes=nodes[0],unknown_boundary_routes=frontiers)
        rows.append(row)
    report={'scope':__doc__,'replay':str(path),'round':42,'queen_body':queen,'visible_pearls':sorted(initial_food),'frozen_visible_others':sorted(occupied),'rows':rows}
    out=Path('test-results/oct9-last30/v270-islands-r42-visible-continuation.json');out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(rows))

if __name__=='__main__':main()
