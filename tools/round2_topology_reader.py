"""Inspect one first-divergence turn using continuous legal baseline observations.

Read-only with respect to frozen candidates and matches. A diagnostic copy adds
selected-candidate prints only. Input stops at the divergent action, so subsequent
baseline observations are never fed after a changed action.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import oct7_reconstruct_portals
from external_panel import source_bundle
from unswbc import clangtool
from unswbc.sandbox import Sandbox

ROOT = Path(__file__).resolve().parents[1]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(out, side, stop):
    candidate = ROOT / 'opponents/generalist-topology-v1'
    source_hash = source_bundle(candidate)[0]
    replay = ROOT / f'test-results/oct7-v5-panel/games/discovery/sas-987/maze-2026100701-{side}/raw.replay'
    who = 0 if side == 'A' else 1
    out.mkdir(parents=True, exist_ok=True)
    oct7_reconstruct_portals.main(['--replay', str(replay), '--out-dir', str(out / 'observations'), '--ids', str(who)])
    fixture_path = out / f'observations/v5-portals-unit{who}-input.json'
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    blocks = re.split(r'(?=^ROUND \d+\n)', fixture['input'], flags=re.M)
    selected = [s for s in blocks[1:] if int(s.splitlines()[0].split()[1]) <= stop]
    inp = blocks[0] + ''.join(s.replace('ENDGAME\n', '') for s in selected) + 'ENDGAME\n'
    (out / 'input.txt').write_text(inp, encoding='utf-8')
    stage = out / 'diagnostic'
    stage.mkdir()
    for p in candidate.iterdir():
        if p.suffix in ('.hpp', '.cpp', '.toml'):
            shutil.copyfile(p, stage / p.name)
    planner = stage / 'planner.hpp'
    text = planner.read_text(encoding='utf-8')
    marker = '    int best=-1,bestGrade=-1,bestContact=-1,bestBirth=-1,bestTerrain=-1;double bestScore=-1e30;'
    assert text.count(marker) == 1
    injection = r'''
    if(m.now==STOP_ROUND)for(int i:selected){const auto& c=candidates[i];
        std::cout<<"CANDIDATE "<<i<<" action=";
        if(c.child>0)std::cout<<"SPLIT"<<c.child;else for(auto d:c.moves)std::cout<<d.value;
        std::cout<<" food="<<c.food<<" paid="<<c.paid<<" uncertain="<<c.uncertain
        <<" grade="<<future_grade(c.future,horizon)<<" depth="<<c.future.depth
        <<" outside="<<c.future.outside<<" tier="<<c.terrain_tier
        <<" finite="<<c.terrain_evidence.finite()<<" remaining="<<c.terrain_evidence.remaining
        <<" score="<<c.score<<" evidence="<<action_evidence::label(c.evidence.status)<<"\n";
    }
'''.replace('STOP_ROUND', str(stop))
    planner.write_text(text.replace(marker, injection + marker), encoding='utf-8')
    (stage / 'main.cpp').write_text(r'''
#include <iostream>
#include "planner.hpp"
int main(){auto [ct,game]=unswbc::init();strategy::Memory memory;planner::State state;
 while(unswbc::update(ct,game)){
  planner::observe(ct,memory,state);memory.remember(ct.get_position());
  auto plan=planner::choose(ct,memory,state);
  std::cout<<"HISTORY "<<game.get_round_num()<<" action=";
  if(plan.action.child_size>0)std::cout<<"SPLIT"<<plan.action.child_size;
  else for(auto d:plan.moves)std::cout<<d.value;
  std::cout<<" note="<<plan.note<<"\n";
  if(game.get_round_num()==STOP_ROUND)break;
  planner::remember(ct,memory,state,plan,game.get_round_num());
 }
}
'''.replace('STOP_ROUND', str(stop)), encoding='utf-8')
    wasm = clangtool.build(stage)
    box = Sandbox(wasm_path=wasm, argv=['diagnostic'], stdin=io.BytesIO(inp.encode()), needs_zygote=False, needs_meter=False)
    code = box.run()
    output = (bytes(box.stdout) + bytes(box.stderr)).decode('utf-8', 'replace')
    (out / 'output.log').write_text(output, encoding='utf-8')
    actual = {int(rd): action for rd, action in re.findall(r'^HISTORY (\d+) action=(\S+)', output, re.M)}
    records = [r for r in fixture['recorded_actions'] if r['round'] <= stop]
    def action(r):
        a = r['action']
        return ''.join(a['steps']) if a['kind'] == 'move' else 'SPLIT' + str(a.get('childSize', a.get('size')))
    errors = [{'round': r['round'], 'actual': actual.get(r['round']), 'expected': action(r)}
              for r in records if r['round'] < stop and actual.get(r['round']) != action(r)]
    assert source_bundle(candidate)[0] == source_hash
    result = {'scope': __doc__, 'matches_run': 0, 'side': side, 'stop_round': stop,
              'candidate_source_sha256': source_hash, 'source_replay_sha256': digest(replay),
              'exporter_sha256': digest(oct7_reconstruct_portals.__file__), 'driver_sha256': digest(__file__),
              'input_sha256': digest(out / 'input.txt'), 'output_sha256': digest(out / 'output.log'),
              'diagnostic_source_sha256': source_bundle(stage)[0], 'diagnostic_wasm_sha256': digest(wasm),
              'exit_code': code, 'prior_actions_verified': len(records) - 1, 'prior_action_mismatches': errors,
              'baseline_action_at_stop': action(records[-1]), 'candidate_action_at_stop': actual.get(stop),
              'printed_candidates': [line for line in output.splitlines() if line.startswith('CANDIDATE ')],
              'passed': code == 0 and not errors and len(actual) == len(records)}
    (out / 'proof.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--side', choices=['A', 'B'], required=True)
    p.add_argument('--stop', type=int, required=True)
    a = p.parse_args()
    run(a.out, a.side, a.stop)
