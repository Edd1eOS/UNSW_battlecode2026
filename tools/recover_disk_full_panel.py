"""Create a separate recovery panel; retain original failed attempts unchanged.

Only the specifically observed replay-write disk-full failure is recoverable.
Copied completed games are reused observations, never additional experiments.
"""
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--original',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    root=Path('test-results').resolve();src=args.original.resolve();dst=args.out.resolve()
    if not src.is_relative_to(root) or not dst.is_relative_to(root) or dst.exists():raise ValueError('New workspace panel required')
    records=[(p,json.loads(p.read_text(encoding='utf8'))) for p in (src/'games').rglob('result.json')]
    failures=[(p,r) for p,r in records if 'infrastructure_error' in r]
    if not failures or any(r['infrastructure_error']!='OSError: [Errno 28] No space left on device' for p,r in failures):
        raise ValueError('Only observed disk-full failures may be retried')
    if any(r['invalid_runtime_events'][r['candidate_team']] or not r['candidate_budget_margin_passed'] for p,r in records):
        raise ValueError('Candidate correctness/budget gates cannot be bypassed')
    if any(not (p/'result.json').exists() for p in (src/'games').glob('*/*/*') if p.is_dir()):raise ValueError('Unrecorded interrupted game')
    dst.mkdir()
    for p in src.iterdir():
        if p.name in ('games','summary.json'):continue
        if p.is_dir():shutil.copytree(p,dst/p.name)
        else:shutil.copy2(p,dst/p.name)
    reused=[]
    for p,r in records:
        if 'infrastructure_error' in r:continue
        replay=p.parent/'raw.replay'
        if hashlib.sha256(replay.read_bytes()).hexdigest()!=r['replay']['sha256']:raise ValueError('Original replay mismatch')
        shutil.copytree(p.parent,dst/p.parent.relative_to(src));reused.append(r['id'])
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'original':str(src),'recovery':str(dst),'reused_completed_games':reused,
            'failed_attempts_retained':[{'id':r['id'],'path':str(p),'result_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                                        'error':r['infrastructure_error']} for p,r in failures],
            'gate':'Source, binary, engine, map, seeds and 90M margin unchanged. Only disk-full replay-write attempts retried in a separate directory. No original record overwritten.'}
    (dst/'recovery.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps({'reused':len(reused),'disk_full_retries':len(failures),'out':str(dst)}))

if __name__=='__main__':main()
