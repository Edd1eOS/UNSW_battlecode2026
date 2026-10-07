"""Offline emergency evidence/cohort scope, never a bot or engine launcher."""
from __future__ import annotations
import argparse,hashlib,json,re,statistics
from collections import Counter
from pathlib import Path
try:
    from . import audit_online,panel_trajectory,oct7_family_capital,oct7_external_panel
except ImportError:
    import audit_online,panel_trajectory,oct7_family_capital,oct7_external_panel

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def flags(note):return {k:int(v) for k,v in re.findall(r'\b(emergency_[a-z_]+)=(-?\d+)',note or '')}

def selected_records(data,team):
    teams={int(d['id']):d['team'] for d in data['initial_dragons']}
    records=[];round_no=None;actor=None;note=None;first={};births=set()
    for e in data['events']:
        kind=e.get('type',e.get('kind'))
        if kind=='roundStart':round_no=int(e['round']);actor=None;note=None
        elif round_no is None:continue
        elif kind=='turnStart':actor=int(e['id']);note=None
        elif kind=='dragonIndicator' and int(e['id'])==actor:note=e.get('text')
        elif kind=='dragonSplit':
            child=int(e['childId']);teams[child]=e['team'];births.add(child)
        elif kind=='dragonAction':
            i=int(e['id']);action=e.get('action')
            if i in births and i not in first:first[i]={'kind':action.get('kind') if isinstance(action,dict) else None,'action':action,'updates':0,'round':round_no}
            if teams.get(i)==team and i==actor:
                f=flags(note)
                selected='emergency_child_no_move' in f
                if selected or f.get('emergency_rejected',0)>0:
                    records.append({'round':round_no,'parent_id':i,'note':note,'flags':f,
                                    'selected_emergency':selected,'action_kind':action.get('kind') if isinstance(action,dict) else None})
        elif kind=='dragonUpdate':
            i=int(e['id'])
            if i in first and round_no==first[i]['round'] and actor==i:first[i]['updates']+=1
        elif kind=='dragonDeath':
            i=int(e['id'])
            if i in first and round_no==first[i]['round'] and actor==i:first[i]['death_reason']=e.get('reason')
    return records,first

def summarize(records):
    selected=[r for r in records if r['selected_emergency']]
    cohorts=[r['two_round'] for r in selected if 'two_round' in r and not r['two_round']['truncated']]
    values=[r['net_retained'] for r in cohorts]
    return {'selected_emergency':len(selected),'reported_child_no_first_move':sum(r['flags'].get('emergency_child_no_move')==1 for r in selected),
            'reported_child_unknown':sum(r['flags'].get('emergency_child_unknown')==1 for r in selected),
            'reported_child_portal':sum(r['flags'].get('emergency_child_portal')==1 for r in selected),
            'reported_child_budget':sum(r['flags'].get('emergency_child_budget')==1 for r in selected),
            'reported_parent_unknown':sum(r['flags'].get('emergency_parent_unknown')==1 for r in selected),
            'reported_parent_no_first_move':sum(r['flags'].get('emergency_parent_no_move')==1 for r in selected),
            'reported_rejected_proposals':sum(r['flags'].get('emergency_rejected',0) for r in records),
            'first_actual_child_actions':dict(Counter(r.get('child_first_action',{}).get('kind') or 'none' for r in selected)),
            'child_no_move_but_first_actual_update':sum(r['flags'].get('emergency_child_no_move')==1 and r.get('child_first_action',{}).get('updates',0)>0 for r in selected),
            'complete_two_round_cohorts':len(cohorts),'truncated_two_round_cohorts':sum(r.get('two_round',{}).get('truncated',False) for r in selected),
            'two_round_net_retained':{'positive':sum(v>0 for v in values),'zero':sum(v==0 for v in values),'negative':sum(v<0 for v in values),
                                      'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None},
            'two_round_all_dead':sum(r['live_count']==0 for r in cohorts)}

def analyze(path):
    capture={}
    def decode(raw):capture['data']=audit_online.load_replay(raw);return capture['data']
    strict=panel_trajectory.analyze_result(path,decoder=decode)
    family=oct7_family_capital.audit_families(capture['data'],strict['trajectory'],strict['details'])
    records,first=selected_records(capture['data'],strict['candidate_team'])
    splits={(s['round'],s['parent_id']):s for s in family['splits'] if s['team']==strict['candidate_team']}
    for r in records:
        if not r['selected_emergency']:continue
        s=splits.get((r['round'],r['parent_id']))
        if s is None:raise ValueError('Selected emergency SPLIT lacks a recorded birth')
        if s['decision_indicator']!=r['note']:raise ValueError('Split indicator differs from current selected turn')
        r.update(child_id=s['child_id'],capital_before=s['capital_before'],parent_after=s['parent_after'],child_birth_capital=s['child_birth_capital'],
                 two_round=s['two_round'],child_first_action=first.get(s['child_id'],{}))
    return {'job_id':strict['job_id'],'map':strict['map'],'team':strict['candidate_team'],'official_outcome':strict['official_outcome'],
            'eligible':strict['eligible_for_mechanism_comparison'],'gross_ledger_verified':strict['details']['gross_ledger_verified'],
            'provenance':strict['provenance'],'summary':summarize(records),'records':records}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--panel',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--comparison',type=Path,required=True,help='Frozen strict paired report to bind verified result/replay identities')
    args=parser.parse_args();plan=oct7_external_panel.read_plan(args.panel);freeze=oct7_external_panel.candidate_record(args.panel)
    comparison=json.loads(args.comparison.read_text(encoding='utf-8'))
    if comparison['arms']['candidate']['candidate_source_bundle_sha256']!=freeze['source_bundle_sha256']:raise ValueError('Comparison candidate source differs')
    verified={str(Path(p['candidate_result']).resolve()):p for p in comparison['pairs'] if not p['issues']}
    jobs=[j for j in plan['jobs'] if j['phase']=='discovery'];reports=[];errors=[]
    for n,j in enumerate(jobs):
        path=args.panel/'games'/j['id']/'result.json'
        try:
            row=json.loads(path.read_text(encoding='utf-8'))
            if row['candidate']!=freeze or row['id']!=j['id']:raise ValueError('Result identity differs from freeze/job')
            paired=verified.get(str(path.resolve()))
            if paired is None:raise ValueError('Result lacks strict verified comparison pair')
            report=analyze(path)
            if report['provenance']!=paired['candidate_provenance']:raise ValueError('Raw identity differs from strict comparison')
            reports.append(report)
        except (OSError,ValueError,KeyError,RuntimeError) as error:errors.append({'job_id':j['id'],'error':str(error)})
        print(json.dumps({'done':n+1,'scheduled':len(jobs),'failed':len(errors)}),flush=True)
    groups={}
    for label,rr in [('all_formal',reports),('candidate_runtime_eligible',[r for r in reports if r['eligible']]),('runtime_ineligible',[r for r in reports if not r['eligible']])]:
        groups[label]={'games':len(rr),'official_outcomes':dict(Counter(r['official_outcome'] for r in rr)),**summarize([x for r in rr for x in r['records']])}
    result={'scope':'Complete raw emergency evidence, not independent strength or causal counterfactual','candidate_freeze':freeze,'scheduled':len(jobs),
            'completed':len(reports),'errors':errors,'groups':groups,'reports':reports,'matches_run':0,
            'comparison_sha256':digest(args.comparison),
            'dependencies':{name:digest(Path(__file__).parent/name) for name in ['oct7_emergency_scope.py','oct7_family_capital.py','panel_trajectory.py','trajectory_metrics.py','audit_online.py','oct7_external_panel.py']},
            'limits':['No-MOVE is not no-SPLIT or inevitable death for long actors','Indicators are model evidence, not food or continuation execution',
                      'A default all-zero assessment is not logged proof of complete/facing-known body','Cohorts overlap; their retained capital is not summed',
                      'Two-round net uses body updates and death capital; cohort gross food/paid remain unknown','Runtime ineligible formal results retained separately']}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'completed':len(reports),'errors':len(errors),'groups':groups}),flush=True)

if __name__=='__main__':main()
