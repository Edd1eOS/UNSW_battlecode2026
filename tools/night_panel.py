"""Oct7 evening: paired external discovery from the actual active v66 base."""
import argparse,json,os
from pathlib import Path
import oct7_external_panel as panel

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','status']);p.add_argument('--candidate');p.add_argument('--out',required=True);p.add_argument('--phase',default='discovery',choices=['discovery','holdout']);a=p.parse_args()
    # Public opponent used only as a reproducible regression panel, never as
    # evidence of 1800 Elo. Keep every official local map and both sides.
    panel.REGISTRY={k:v for k,v in panel.REGISTRY.items() if k=='sas-987'}
    panel.SEEDS={'discovery':(2026100741,), 'holdout':(2026100749,)}
    out=panel.ROOT/a.out;os.environ['UNSWBC_WARM']='1'
    if a.command=='prepare':
        plan=panel.plan_panel(out,panel.ROOT/'maps/current',panel.SEEDS)
        panel.protocol_check(out)
        panel.freeze_candidate(out,(panel.ROOT/a.candidate).resolve(),Path(a.candidate).name)
        print(json.dumps({'planned':len(plan['jobs']),'panel':str(out)}))
    elif a.command=='run':panel.run_panel(out,a.phase,None)
    else:print(json.dumps(panel.status(out,panel.read_plan(out))))

if __name__=='__main__':main()
