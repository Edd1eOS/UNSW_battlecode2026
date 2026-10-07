"""Offline functional evidence comparison; no engines or bot executions."""
import hashlib,json
from pathlib import Path
from tools.audit_online import load_replay

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def physical_births(panel,job):
 path=Path(panel)/'games'/job/'result.json';row=json.loads(path.read_text(encoding='utf-8'))
 raw=Path(row['replay']['path']);raw=raw if raw.is_absolute() else path.parent/raw
 if sha(raw)!=row['replay']['sha256']:raise ValueError('Replay hash mismatch')
 data=load_replay(raw);rr=None;prefix=hashlib.sha256(canonical({'map':data['map'],'seed':data['seed'],'initial':data['initial_dragons']}));records={}
 for event in data['events']:
  k=event['type']
  if k=='roundStart':rr=event['round']
  if k=='dragonSplit' and rr is not None:
   records[(rr,event['parentId'])]={'prefix_sha256':prefix.hexdigest(),'birth':event,
                                  'body_sha256':hashlib.sha256(canonical([event['parentBody'],event['childBody']])).hexdigest()}
  if k=='dragonAction':normalized={'type':k,'id':event['id'],'action':event.get('action')}
  elif k in ('roundStart','turnStart','dragonUpdate','dragonSplit','dragonDeath','tileChange'):normalized=event
  else:continue
  prefix.update(canonical(normalized)+b'\n')
 return records

oldpath=Path('test-results/oct7-emergency-scope.json');newpath=Path('test-results/oct7-emergency-v2-scope.json')
old=json.loads(oldpath.read_text(encoding='utf-8'));new=json.loads(newpath.read_text(encoding='utf-8'))
if old['errors'] or new['errors']:raise ValueError('Incomplete scope report')
byjob={r['job_id']:r for r in new['reports']};rows=[]
for game in old['reports']:
 targets=[r for r in game['records'] if r['selected_emergency'] and r['flags'].get('emergency_child_no_move')==1 and r['child_first_action'].get('updates',0)>0]
 if not targets:continue
 job=game['job_id'];current=byjob[job];decisions={(r['round'],r['parent_id']):r for r in current['records'] if r['selected_emergency']}
 before=physical_births('test-results/oct7-emergency-panel',job);after=physical_births('test-results/oct7-emergency-v2-panel',job)
 for r in targets:
  key=(r['round'],r['parent_id']);matched=decisions.get(key);a=before[key];b=after.get(key)
  same_prefix=b is not None and a['prefix_sha256']==b['prefix_sha256'];same_birth=b is not None and a['birth']==b['birth']
  rows.append({'job_id':job,'eligible':game['eligible'],'round':r['round'],'parent_id':r['parent_id'],'old_child_id':r['child_id'],
               'physical_prefix_same':same_prefix,'physical_birth_same':same_birth,'old_birth_body_sha256':a['body_sha256'],
               'new_birth_body_sha256':b['body_sha256'] if b else None,'v2_selected_at_same_decision':matched is not None,
               'v2_flags':matched['flags'] if matched else None,'v2_child_first_action':matched['child_first_action'] if matched else None,
               'old_raw_provenance':game['provenance'],'new_raw_provenance':current['provenance']})
contradictions=[{'job_id':g['job_id'],'eligible':g['eligible'],'record':r} for g in new['reports'] for r in g['records']
               if r['selected_emergency'] and r['flags'].get('emergency_child_no_move')==1 and r['child_first_action'].get('updates',0)>0]
summary={'old_recorded_contradictions':len(rows),'old_eligible_contradictions':sum(r['eligible'] for r in rows),
         'same_physical_prefix_and_birth':sum(r['physical_prefix_same'] and r['physical_birth_same'] for r in rows),
         'v2_matched_decisions':sum(r['v2_selected_at_same_decision'] for r in rows),
         'matched_now_unknown':sum(r['v2_flags'] is not None and r['v2_flags'].get('emergency_child_unknown')==1 for r in rows),
         'v2_actual_selected_contradictions':len(contradictions),'v2_eligible_selected_contradictions':sum(r['eligible'] for r in contradictions)}
result={'scope':'Functional raw replay comparison; no counterfactual strength or saved-unit claim','summary':summary,'records':rows,
        'v2_actual_selected_contradictions':contradictions,'matches_run':0,
        'scope_reports_sha256':{'v1':sha(oldpath),'v2':sha(newpath)},'driver_sha256':sha(__file__),
        'prefix_basis':'Initial bodies/map/seed and executed actions, updates, splits, deaths, tile and turn events; model notes/instruction counts excluded',
        'limit':'Matched recorded states establish evidence annotation behavior, not improved survival or income'}
Path('test-results/emergency-v2-selected-evidence-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
