"""Execute the retained C++ contract WASMs, binding exact executed bytes.

This closes the artifact-retention audit after the official compiler's external
cache was re-resolved. It does not execute production games or measure CPU.
"""
import hashlib
import json
from pathlib import Path
from unswbc.sandbox import Sandbox

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    source=ROOT/'test-results/round2-final-cpp-checks.json'
    checked=json.loads(source.read_text(encoding='utf-8'))
    assert checked['passed']
    records=[]
    for row in checked['checks']:
        wasm=ROOT/row['stage']/'executed.wasm'
        digest=hashlib.sha256(wasm.read_bytes()).hexdigest()
        assert digest==row['wasm_files']['executed.wasm']
        box=Sandbox(wasm_path=wasm,argv=['retained-check'],needs_zygote=False,needs_meter=False)
        code=box.run()
        records.append({'test':row['test'],'dependency_sha256':row['dependency_sha256'],
                        'wasm_sha256':digest,'exit_code':code,
                        'stdout':bytes(box.stdout).decode('utf-8','replace'),
                        'stderr':bytes(box.stderr).decode('utf-8','replace')})
    result={'scope':__doc__,'matches_run':0,'passed':all(r['exit_code']==0 for r in records),
            'source_record_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':records}
    (ROOT/'test-results/round2-retained-cpp-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checks':len(records),'passed':result['passed']}))
    if not result['passed']:raise SystemExit(1)
