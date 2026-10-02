"""Verify a worker's paid, two-step Queen interception in the official sandbox."""
import argparse
import contextlib
import hashlib
import io
import json
import re
from pathlib import Path
from unswbc import clangtool
from unswbc.run import execute
from unswbc.sandbox import SandboxBot

parser=argparse.ArgumentParser();parser.add_argument('--candidate',default='bot');parser.add_argument('--ordinary',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'test-results'/'tactics-engine';out.mkdir(parents=True,exist_ok=True)
files=sorted(p for p in (ROOT/args.candidate).iterdir() if p.suffix in ('.cpp','.hpp','.toml'))
digest=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in files)).hexdigest()
stage=ROOT/'test-results'/'build'/digest[:16];stage.mkdir(parents=True,exist_ok=True)
for p in files:(stage/p.name).write_bytes(p.read_bytes())
ours=str(clangtool.build(stage))
enemy=out/'north';enemy.mkdir(exist_ok=True)
(enemy/'bot.toml').write_bytes((ROOT/'bot/bot.toml').read_bytes())
(enemy/'helper.hpp').write_bytes((ROOT/'bot/helper.hpp').read_bytes())
(enemy/'main.cpp').write_text('#include "helper.hpp"\nint main(){auto [c,g]=unswbc::init();while(unswbc::update(c,g)){c.make_move(unswbc::Direction::NORTH);unswbc::end_turn();}}\n')
theirs=str(clangtool.build(enemy))
map_path=out/'intercept.map'
map_path.write_text('MAP 15 15\nMAP_NAME Interception\nTILE_COUNT 0\nEDGE_COUNT 0\nDRAGON_COUNT 7\nDRAGON 0 3 1 11 1 10 1 9\nDRAGON 1 3 7 6 7 7 7 8\nDRAGON 0 4 5 5 4 5 3 5 2 5\nDRAGON 1 2 11 3 11 4\nDRAGON 0 2 3 1 2 1\nDRAGON 1 2 8 12 8 13\nDRAGON 0 2 12 10 12 11\nEND\n')
if args.ordinary:
    text=map_path.read_text(encoding='utf-8')
    text=text.replace('DRAGON 1 3 7 6 7 7 7 8','DRAGON 1 2 11 2 11 3')
    text=text.replace('DRAGON 1 2 11 3 11 4','DRAGON 1 7 7 5 7 6 7 7 8 7 8 6 8 5 8 4')
    map_path.write_text(text,encoding='utf-8')
original=SandboxBot.ask;turns=[]
def capture(self,block):
    reply=original(self,block)
    turns.append(dict(id=self._name,input=block.decode(),output=reply.decode()))
    return reply
SandboxBot.ask=capture
log=io.StringIO()
try:
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        code=execute(str(map_path),[ours,theirs],False,out/'intercept.replay',False,True,seed=17)
finally:SandboxBot.ask=original
text=log.getvalue();(out/'engine.log').write_text(text,encoding='utf-8')
worker=next(t for t in turns if t['id']=='2')
assert code==0 and ('ATTACK_LARGE_WORKER' if args.ordinary else 'ATTACK_QUEEN') in worker['output'],text
assert 'MOVE EE' in worker['output'],worker
assert f'bot {3 if args.ordinary else 1} (team B) died: lost a head-to-head' in text,text
assert 'bot 2 (team A) died: lost a head-to-head' in text,text
assert not re.search('no valid action|sandbox error|exhaust|timed out',text),text
report=dict(source_hash=digest,worker_action=worker['output'],verified='With four allied units, worker spends one segment to intercept a visible enemy head in two steps.',target='worker' if args.ordinary else 'queen')
(out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
