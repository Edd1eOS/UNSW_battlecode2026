"""Bind round-three experiments, comparisons and online probes to exact artifacts."""
import hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('test-results');STUDY=ROOT/'oct7-highrank-study';DOC=Path('docs')
PANELS={
 'colony-lifecycle-v1':['colony-lifecycle-v1-external','colony-lifecycle-v1-kgts'],
 'capital-transfer-v1':['capital-transfer-v1-external','capital-transfer-v1-kgts-recovered'],
 'adversarial-reply-v1':['adversarial-reply-v1-external-recovered','adversarial-reply-v1-kgts-recovered'],
 'adversarial-reply-v2':['adversarial-reply-v2-external'],
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def panel(name):
    root=ROOT/name;freeze=read(root/'candidate/freeze.json');rows=[]
    for path,entry in freeze['source_files'].items():assert sha(Path(path))==entry['sha256'],path
    assert sha(root/'candidate/bot.wasm')==freeze['wasm_sha256']
    for p in sorted((root/'games').rglob('result.json')):
        r=read(p);raw=p.parent/'raw.replay'
        if r.get('replay'):assert sha(raw)==r['replay']['sha256'],str(raw)
        rows.append({k:r[k] for k in ('id','phase','map','seed','candidate_team','opponent_team','map_sha256',
            'formal_result','official_outcome','eligible_mechanism_result','invalid_runtime_events','candidate_budget_margin_passed','peak') if k in r}
            |{'result_file':str(p),'result_sha256':sha(p),'replay_sha256':r.get('replay',{}).get('sha256'),
              'opponent':r['opponent'],'source_sha256':r['candidate']['source_bundle_sha256']})
    return {'plan_sha256':sha(root/'plan.json'),'freeze':freeze,'summary':read(root/'summary.json') if (root/'summary.json').exists() else None,
            'recovery':read(root/'recovery.json') if (root/'recovery.json').exists() else None,'rows':rows}
def main():
    candidates={k:{p:panel(p) for p in ps} for k,ps in PANELS.items()};comparisons={}
    for name in PANELS:
        for suffix in ('comparison','kgts-comparison'):
            p=ROOT/f'{name}-{suffix}.json'
            if p.exists():
                r=read(p);comparisons[p.stem]={'file':str(p),'sha256':sha(p),'arms':r['arms'],'denominators':r['denominators'],'summary':r['summary']}
    probes={}
    for name in ('colony-online-baseline','capital-transfer-online','adversarial-reply-online'):
        root=ROOT/name;r=read(root/'analysis.json')
        probes[name]={'summary':r['summary'],'analysis_sha256':sha(root/'analysis.json'),
            'matches':[{k:m[k] for k in ('match_id','raw_sha256','metadata','quality','final','gross_verified','queen_deaths')} for m in r['matches']],
            'deliveries':read(root/'deliveries.json') if (root/'deliveries.json').exists() else None,
            'queen_contacts':read(root/'queen-contacts.json') if (root/'queen-contacts.json').exists() else None}
    failures=[]
    for name in ('capital-transfer-v1-kgts','adversarial-reply-v1-external','adversarial-reply-v1-kgts'):
        for p in (ROOT/name/'games').rglob('result.json'):
            r=read(p)
            if 'infrastructure_error' in r:failures.append({'path':str(p),'sha256':sha(p),'id':r['id'],'error':r['infrastructure_error']})
    docs={}
    for p in STUDY.glob('*.json'):
        if p.name not in ('analysis.json','one-inspect.json','imports.json','selection.json','summary.json','resource-provenance.json','series-ui.json'):
            docs[p.name]={'sha256':sha(p),'contents':read(p)}
    contract_paths=[ROOT/'capital-transfer-contract/result.json',ROOT/'reply-physics-contract/result.json']
    new_completed=sum(bool(r.get('formal_result')) for group in candidates.values() for p in group.values() for r in p['rows'])
    online_count=sum(len(p['matches']) for p in probes.values())
    delivery_paths=[ROOT/'capital-transfer-v1-deliveries.json',ROOT/'capital-transfer-v1-kgts-deliveries.json']
    tool_paths=sorted(set(Path('tools').glob('highrank_*.py')) | set(Path('tools').glob('capital_transfer_*.py')) |
                      {Path('tools/queen_contact_audit.py'),Path('tools/reply_physics_contract.py'),Path('tools/recover_disk_full_panel.py')})
    out={'created_utc':datetime.now(timezone.utc).isoformat(),'learning_games':100,
         'new_completed_local_external_games':new_completed,'online_probe_games':online_count,
         'retained_infrastructure_failed_attempts':failures,'candidates':candidates,'comparisons':comparisons,'online_probes':probes,
         'contracts':{str(p):{'sha256':sha(p),'contents':read(p)} for p in contract_paths},
         'mechanism_delivery_reports':{str(p):{'sha256':sha(p),'contents':read(p)} for p in delivery_paths},
         'measurement_tools':{str(p):sha(p) for p in tool_paths},
         'plans_and_ui':docs,'cpp_check_log':{'path':str(STUDY/'cpp-final-checks.log'),'sha256':sha(STUDY/'cpp-final-checks.log'),
                      'contents':(STUDY/'cpp-final-checks.log').read_text(encoding='utf8')},
         'notes':['Recovery copied completed games are counted once; original failed replay writes retained separately.',
                  'Old V5 reference games are not new experiments. No candidate-vs-candidate games.',
                  'Learning100, local experiments and online validation are different populations, not a pooled win rate.',
                  'Unopened holdout remains unopened. No tested candidate adopted solely from discovery results.']}
    (DOC/'oct7-highrank-experiment-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'completed_local':new_completed,'infra_attempts':len(failures),'online':online_count}))

if __name__=='__main__':main()
