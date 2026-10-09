"""Audit public online replays; never runs bots or modifies website state."""
import argparse
from collections import Counter
import json
from pathlib import Path
from audit_online import load_replay

def audit(path):
    d=load_replay(path,node_path='D:/node/node.exe')
    live={v['id']:{'team':v['team'],'body':[(p['x'],p['y']) for p in v['body']]} for v in d['initial_dragons']}
    stats={t:{'moves':0,'splits':0,'sonar':0,'paid_steps_requested':0,'pearls_taken':0,'death_reasons':Counter(),'first_length4':{},'first_split':None,'peak_units':sum(v['team']==t for v in live.values()),'instruction_peak':0,'instruction_exceeded':0,'r50':None} for t in 'AB'}
    rnd=-1;actor=None;action_started=False;traces=[]
    for e in d['events']:
        k=e['type']
        if k=='roundStart':
            rnd=e['round'];actor=None
            if rnd==50:
                for t in 'AB':
                    bodies=[v['body'] for v in live.values() if v['team']==t]
                    stats[t]['r50']={'units':len(bodies),'total_length':sum(map(len,bodies))}
        elif k=='turnStart':actor=e['id']
        elif k=='dragonAction':
            i=e['id'];v=live[i];t=v['team'];a=e.get('action');action_started=True
            if not a:continue
            length=len(v['body']);s=stats[t]
            if i<4 and length>=4 and str(i) not in s['first_length4']:s['first_length4'][str(i)]=rnd
            if a['kind']=='move':
                s['moves']+=1;s['paid_steps_requested']+=max(0,len(a['steps'])-(length+3)//4)
            if rnd<12 and i<4:traces.append({'round':rnd,'id':i,'team':t,'length_before':length,'head':v['body'][0],'action':a})
            ins=e.get('instructions',{});s['instruction_peak']=max(s['instruction_peak'],ins.get('count',0));s['instruction_exceeded']+=bool(ins.get('exceeded'))
        elif k=='tileChange' and not e['hasPearl'] and actor in live:
            stats[live[actor]['team']]['pearls_taken']+=1
        elif k=='dragonUpdate':
            # The replay begins with state announcements, not extra movements.
            if not action_started:continue
            v=live[e['id']];head=(e['head']['x'],e['head']['y']);tail=(e['tail']['x'],e['tail']['y'])
            v['body'].insert(0,head)
            while len(v['body'])>1 and v['body'][-1]!=tail:v['body'].pop()
        elif k=='dragonSplit':
            t=e['team'];s=stats[t];s['splits']+=1
            if s['first_split'] is None:s['first_split']=rnd
            live[e['parentId']]['body']=[(a['x'],a['y']) for a in e['parentBody']]
            live[e['childId']]={'team':t,'body':[(a['x'],a['y']) for a in e['childBody']]}
            s['peak_units']=max(s['peak_units'],sum(v['team']==t for v in live.values()))
        elif k=='dragonDeath':
            v=live.pop(e['id']);stats[v['team']]['death_reasons'][e['reason']]+=1
            if e['id']<=1:stats[v['team']]['queen_death_round_zero_based']=rnd
        elif k=='sonarPing' and e['senderId'] in live:stats[live[e['senderId']]['team']]['sonar']+=1
    return {'path':str(path),'sha256':d['input_sha256'],'teams':d['teams'],'result':d['result'],'stats':stats,'opening':traces,'rounds':rnd+1,'scope':'Observed replay metrics. Paid steps are requested not guaranteed executed. Round indices are zero based. Pearl count assumes tile removal within a turn is consumption.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('replays',nargs='+',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    rows=[audit(f) for f in a.replays];a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    for r in rows:print(json.dumps({k:r[k] for k in ('path','teams','result','stats')},ensure_ascii=True),flush=True)
if __name__=='__main__':main()
