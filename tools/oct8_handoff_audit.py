"""Audit actual transfer receipts and same-turn handoff markers."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from audit_online import load_replay
ROOT=Path(__file__).resolve().parents[1]/'test-results/oct8-handoff'
def one(path):
 d=load_replay(path,node_path='D:/node/node.exe');b={v['id']:[(p['x'],p['y']) for p in v['body']] for v in d['initial_dragons']};team={v['id']:v['team'] for v in d['initial_dragons']}
 rnd=0;actor=None;note='';expected={};pearls={};donors=[];receipts=[];handoffs=[];death={};active=None
 for e in d['events']:
  k=e['type']
  if k=='roundStart':rnd=e['round']
  elif k=='turnStart':actor=e['id'];note='';expected={};active=None
  elif k=='dragonIndicator':
   if e['id']==actor:note=e['text']
  elif k=='dragonSplit':
   if 'CAPITAL_HANDOFF' in note:
    handoffs.append({'round':rnd,'parent':e['parentId'],'child':e['childId'],'child_length':len(e['childBody'])})
   for i,key in [(e['parentId'],'parentBody'),(e['childId'],'childBody')]:b[i]=[(p['x'],p['y']) for p in e[key]];team[i]=e['team']
  elif k=='dragonDeath':
   i=e['id'];body=b.pop(i);death[i]={'round':rnd,'reason':e['reason']}
   tag=None
   if i==actor and 'LOCAL_TRANSFER' in note:
    tag={'id':i,'round':rnd,'team':team[i],'length':len(body),'pearls':len(body[::2]),'target':int(note.split('recipient=')[1]),'reason':e['reason']};donors.append(tag)
   expected={p:tag for p in body[::2]}
  elif k=='tileChange':
   p=(e['tile']['x'],e['tile']['y'])
   if e['hasPearl']:pearls[p]=expected.pop(p,None)
   else:
    tag=pearls.pop(p,None)
    if tag:receipts.append({'round':rnd,'recipient':actor,'recipient_team':team[actor],'recipient_length':len(b[actor]),'lag':rnd-tag['round'],'donor':tag})
  elif k=='dragonUpdate':
   i=e['id'];body=[(e['head']['x'],e['head']['y']),*b[i]];tail=(e['tail']['x'],e['tail']['y'])
   while len(body)>1 and body[-1]!=tail:body.pop()
   b[i]=body
 for h in handoffs:h['child_death']=death.get(h['child'])
 counts=Counter()
 for r in receipts:
  same=r['recipient_team']==r['donor']['team'];counts['own' if same else 'enemy']+=1
  if same:counts['queen' if r['recipient']<=1 else 'large_worker' if r['recipient_length']>=8 else 'small_worker']+=1
  counts['intended_target']+=r['recipient']==r['donor']['target']
 return {'path':str(path),'source_sha256':d['input_sha256'],'handoffs':handoffs,'donors':donors,'receipts':receipts,'receipt_counts':dict(counts),'donor_pearls':sum(x['pearls'] for x in donors)}
if __name__=='__main__':
 paths=list((ROOT/'discovery/handoff/games').glob('*/raw.replay'))+list((ROOT/'strict-frozen-discovery/strict/games').glob('*/raw.replay'))+list((ROOT/'delivery-discovery/delivery/games').glob('*/raw.replay'))+list((ROOT/'delivery-validation/delivery/games').glob('*/raw.replay'))
 prior=ROOT/'mechanism-audit.json'
 cache={r['path']:r for r in json.loads(prior.read_text(encoding='utf8'))['matches']} if prior.exists() else {}
 pending=[p for p in paths if str(p) not in cache]
 with ThreadPoolExecutor(max_workers=3) as p:
  for r in p.map(one,pending):cache[r['path']]=r
 rows=[cache[str(p)] for p in paths]
 (ROOT/'mechanism-audit.json').write_text(json.dumps({'matches':rows},indent=2),encoding='utf8')
 for group in ['discovery/handoff','strict-frozen-discovery/strict','delivery-discovery/delivery','delivery-validation/delivery']:
  rr=[r for r in rows if group in r['path'].replace('\\','/')];c=Counter()
  for r in rr:c.update(r['receipt_counts'])
  print(group,'games',len(rr),'handoffs',sum(len(r['handoffs']) for r in rr),'donors',sum(len(r['donors']) for r in rr),'pearls',sum(r['donor_pearls'] for r in rr),'receipts',dict(c),flush=True)
