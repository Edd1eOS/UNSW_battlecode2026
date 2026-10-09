"""Reproduce the v118 Australia failure and log its evaluated candidates.

Instrumentation only: actions must remain identical through the fatal turn.
The resulting logs are diagnostic observations, not a strength experiment.
"""
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
stage = ROOT / 'test-results/night-v118-fatal-scores'
shutil.copytree(ROOT / 'opponents/v118-newborn-threat', stage, dirs_exist_ok=True)
path = stage / 'forage.hpp'
source = path.read_text(encoding='utf8')
needle = '            if(viable>best_viable ||'
assert source.count(needle) == 1
diagnostic = '''            if(ct.get_id()==1 && m.now==84) {
                std::cout<<"LOG CAND ";for(auto dd:path)std::cout<<char(dd.value);
                std::cout<<" score "<<score<<" viable "<<viable<<" future "<<future.depth<<" uncertain "<<future.uncertain<<" danger "<<danger[m.index(end)]<<" end "<<end.x<<","<<end.y<<"\\n";
            }
'''
path.write_text(source.replace(needle, diagnostic + needle), encoding='utf8')
output = ROOT / 'test-results/oct7-night-v118-fatal-scores.json.gz'
subprocess.run([sys.executable, str(ROOT / 'tools/replay_policy_probe.py'),
    '--candidate', str(stage), '--observations', str(ROOT / 'test-results/oct7-night-goated-v23-diagnostic-observations'),
    '--out', str(output), '--team', 'A'], check=True, cwd=ROOT)
rows = json.loads(gzip.decompress(output.read_bytes()))['rows']
assert len(rows) == 1 and rows[0]['all_equal'] and rows[0]['checked'] == 85
assert not rows[0]['restarts']
print(rows[0]['turns'][-1]['output'])
