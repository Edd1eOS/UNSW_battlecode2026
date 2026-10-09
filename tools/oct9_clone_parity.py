"""Check extracted training features against the actual WASM runtime features."""
import importlib.util,json,shutil,sys
from pathlib import Path
import numpy as np
from oct8_imitation import features
from oct7_exploration_death_audit import Board
from verify_candidate import build
from unswbc.sandbox import WasmPool,SandboxBot
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'external-benchmarks/smoke_external.py');packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(packet)
stage=ROOT/'test-results/oct9-imitation/parity-bot';stage.mkdir(exist_ok=True)
for f in (ROOT/'opponents/v257-topnine-clone').glob('*.hpp'):shutil.copyfile(f,stage/f.name)
shutil.copyfile(ROOT/'opponents/v257-topnine-clone/bot.toml',stage/'bot.toml')
(stage/'main.cpp').write_text('''#include "imitation.hpp"
#include <iomanip>
int main(){auto [ct,game]=unswbc::init();strategy::Memory m;
while(unswbc::update(ct,game)){m.observe(ct);m.remember(ct.get_position());imitation::Local local(ct,m);
for(auto d:unswbc::Direction::get_direction_list()){imitation::Features f{};if(!local.features(d,f))continue;
std::cout<<"LOG FEATURE "<<strategy::Atlas::direction_index(d);for(double x:f)std::cout<<" "<<std::setprecision(10)<<x;std::cout<<"\\n";}
ct.make_moves({ct.get_dir()});unswbc::end_turn();}}
''')
wasm,digest=build(stage);pool=WasmPool([str(wasm)],key='imitation-parity-v257');records=[]
cases=[([(5,5),(4,5)],[(6,5),(7,4)],[]),
 ([(5,5),(4,5),(3,5)],[(5,4),(6,4)],[(20,[(7,5),(8,5)]),(1,[(5,7),(5,8)])]),
 ([(0,5),(1,5)],[(19,5),(18,4)],[(20,[(19,7),(18,7)])])]
try:
 for no,(body,pearls,enemies) in enumerate(cases):
  raw=packet.frame(3,body,round_num=123,units=5,pearls=pearls,enemies=enemies)
  bot=SandboxBot(pool,init=b'ID 3\nTEAM A\nMAP 20 20\nUNIT_LIMIT 64\n',name=str(no))
  try:output=bot.ask(raw.encode()).decode()
  finally:bot.stop()
  live={3:{'team':'A','body':body},**{i:{'team':'B','body':b} for i,b in enemies}}
  X,valid=features(Board('MAP 20 20'),live,set(pearls),{}, {3:[body[0]]},3,{3:'E' if no<2 else 'W'},123)
  cpp={int(a[2]):np.array(list(map(float,a[3:]))) for line in output.splitlines() if (a:=line.split())[:2]==['LOG','FEATURE']}
  assert set(cpp)==set(np.flatnonzero(valid)),(cpp,valid,output)
  error=max(float(np.abs(cpp[i]-X[i]).max()) for i in cpp)
  assert error<1e-6,(no,error,cpp,X)
  records.append({'fixture':no,'max_absolute_error':error})
finally:pool.close()
(ROOT/'test-results/oct9-imitation/movement-feature-parity.json').write_text(json.dumps({'passed':True,'records':records,'source':digest},indent=2))
print(json.dumps({'passed':True,'records':records}))
