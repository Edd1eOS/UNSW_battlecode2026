"""Keep recorded baseline decisions until one turn, then switch only that decision."""
from pathlib import Path
import argparse
import json
import re
import shutil
from unswbc.sandbox import SandboxBot, WasmPool
from tools.verify_candidate import build

MAIN = r'''#include "helper.hpp"
#include "baseline_human.hpp"
#include "human.hpp"
int main(){
 auto [ct,game]=unswbc::init(); strategy::Memory memory;
 baseline::State old_state; human::State new_state;
 while(unswbc::update(ct,game)){
  memory.observe(ct);memory.remember(ct.get_position());
  human::Plan plan{{ct.get_dir(),0},{},""};
  if(game.get_round_num()<SWITCH_ROUND){
   auto old=baseline::choose(ct,memory,old_state);plan={old.action,old.moves,old.note};
  } else {
   if(game.get_round_num()==SWITCH_ROUND){
    new_state.goal=old_state.goal;new_state.last_portal=old_state.last_portal;
    new_state.queen_brood_done=old_state.queen_brood_done;
   }
   plan=human::choose(ct,memory,new_state);
  }
  ct.set_indicator_string(plan.note);
  if(plan.action.child_size){
   ct.do_split(plan.action.child_size);
   if(ct.get_id()<=1&&plan.note.find(" FLOOD ")!=std::string::npos){
    if(game.get_round_num()<SWITCH_ROUND)old_state.queen_brood_done=true;
    else new_state.queen_brood_done=true;
   }
  }else ct.make_moves(plan.moves);
  strategy::remember_action(ct,memory,plan.action,plan.moves,game.get_round_num());
  unswbc::end_turn();
 }
}
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--round', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = args.out / 'harness-source'
    source.mkdir(parents=True, exist_ok=True)
    for file in args.candidate.iterdir():
        if file.is_file() and file.suffix in ('.cpp', '.hpp', '.h', '.toml'):
            shutil.copyfile(file, source / file.name)
    original = (args.baseline / 'human.hpp').read_text(encoding='utf-8')
    assert original.count('namespace human {') == 1
    (source / 'baseline_human.hpp').write_text(original.replace('namespace human {', 'namespace baseline {'), encoding='utf-8')
    (source / 'main.cpp').write_text(MAIN.replace('SWITCH_ROUND', str(args.round)), encoding='utf-8')
    wasm, digest = build(source)
    history = json.loads(args.history.read_text())
    raw = history['input']
    header = raw[:raw.index('ROUND ')]
    frames = [s.split('ENDGAME')[0] for s in re.split(r'(?=ROUND \d+\n)', raw[raw.index('ROUND '):]) if s.startswith('ROUND ')]
    pool = WasmPool([str(wasm)], key='controlled-switch-' + digest[:24])
    bot = SandboxBot(pool, init=header.encode(), name='controlled-queen')
    rows = []
    try:
        for frame, ref in zip(frames, history['recorded_actions']):
            output = bot.ask(frame.encode()).decode()
            action = re.findall(r'^(?:MOVE [NESW]+|SPLIT \d+)$', output, re.M)
            old = ref['action']
            expected = 'MOVE ' + ''.join(old['steps']) if old['kind'] == 'move' else 'SPLIT ' + str(old['childSegmentCount'])
            row = dict(round=ref['round'], actions=action, baseline_action=expected,
                       matches_baseline=action == [expected], output=output, points=bot.live[0], error=bot.error)
            rows.append(row)
            if ref['round'] < args.round and not row['matches_baseline']:
                raise RuntimeError('Baseline prefix diverged before intervention: ' + json.dumps(row))
            if ref['round'] == args.round:
                break
    finally:
        bot.stop()
        pool.close()
    result = dict(scope='Baseline history reproduced exactly until one intervention decision; no invented observations after divergence, no game-strength inference.',
                  baseline=str(args.baseline), candidate=str(args.candidate), intervention_round=args.round,
                  harness_source_sha256=digest, prefix_all_match=all(r['matches_baseline'] for r in rows[:-1]),
                  prefix_frames=len(rows) - 1, intervention=rows[-1], rows=rows)
    (args.out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))

if __name__ == '__main__':
    main()
