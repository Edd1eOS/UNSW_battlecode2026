"""Generate a choose-only intervention after a strict original replay prefix.

Only original actions update Memory. Public goal/brood/portal state is recovered
from original indicators; the test candidate is called on copies at requested
turns and cannot influence later fixture frames.
"""
import argparse,gzip,json,os,re
from pathlib import Path
from audit_online import load_replay

MAIN=r'''#include "INCLUDE"
#include <cassert>
#include <iostream>
const char* commands[]=COMMANDS; bool floods[]=FLOODS; int goals[]=GOALS; bool portals[]=PORTALS;
int main(){auto [ct,game]=unswbc::init();strategy::Memory m;human::State state;int k=0;
while(unswbc::update(ct,game)){m.observe(ct);m.remember(ct.get_position());human::Plan p{{ct.get_dir(),0},{},"recorded_prefix"};int r=game.get_round_num();
if(CONDITION){assert((int)m.body.size()==ct.get_length());auto mp=m;auto sp=state;auto actual=human::choose(ct,mp,sp);std::cout<<"LOG INTERVENTION VERSION round="<<r<<" memory_len="<<m.body.size()<<" ct_length="<<ct.get_length()<<" recorded_goal="<<state.goal<<" brood="<<state.queen_brood_done<<" visits="<<m.visits(ct.get_position())<<" "<<actual.note<<" ACTION ";if(actual.action.child_size)std::cout<<"SPLIT "<<actual.action.child_size;else{std::cout<<"MOVE ";for(auto d:actual.moves)std::cout<<(char)d.value;}std::cout<<"\n";}
std::string cmd=commands[k];if(cmd.rfind("SPLIT ",0)==0){p.action.child_size=std::stoi(cmd.substr(6));if(floods[k])state.queen_brood_done=true;}else if(cmd.rfind("MOVE ",0)==0){for(char c:cmd.substr(5))p.moves.push_back(unswbc::Direction(c));p.action.direction=p.moves.front();}
if(goals[k]!=-2)state.goal=goals[k];if(portals[k])state.last_portal=r;
if(p.action.child_size)ct.do_split(p.action.child_size);else ct.make_moves(p.moves);strategy::remember_action(ct,m,p.action,p.moves,r);unswbc::end_turn();++k;}}
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--observations',type=Path,required=True);p.add_argument('--id',type=int,required=True);p.add_argument('--rounds',type=int,nargs='+',required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 evidence=json.loads(gzip.decompress(a.observations.read_bytes()));assert evidence['physical_events_equal'] and 'sonar events equal' in evidence['scope']
 q=evidence['queens'][str(a.id)];frames=[f for f in q['frames'] if f['round']<=max(a.rounds)]
 d=load_replay(Path(evidence['source']),node_path='D:/node/node.exe');width=int(d['map'].splitlines()[0].split()[1]);indicators={};rnd=None
 for e in d['events']:
  if e['type']=='roundStart':rnd=e['round']
  elif e['type']=='dragonIndicator' and e['id']==a.id:indicators[rnd]=e['text']
 commands=[];floods=[];goals=[];portals=[];restored=[]
 for f in frames:
  note=indicators.get(f['round'],'');goal=re.search(r'target=(-?\d+),(-?\d+)',note);scalar=re.search(r'goal=(-?\d+)',note)
  value=(int(goal[1])+width*int(goal[2]) if int(goal[1])>=0 else -1) if goal else int(scalar[1]) if scalar else -2
  commands.append(f['action']);floods.append(' FLOOD ' in note);goals.append(value);portals.append(' PORTAL_' in note)
  restored.append({'round':f['round'],'action':f['action'],'goal_after':value,'flood':floods[-1],'portal':portals[-1],'indicator':note})
 a.out.mkdir(parents=True,exist_ok=True)
 def arr(items):return json.dumps(items,separators=(',',':')).replace('[','{').replace(']','}')
 cpp=MAIN.replace('INCLUDE',Path(os.path.relpath(a.candidate/'human.hpp',a.out)).as_posix()).replace('COMMANDS',arr(commands)).replace('FLOODS',arr(floods)).replace('GOALS',arr(goals)).replace('PORTALS',arr(portals)).replace('CONDITION',' || '.join(f'r=={r}' for r in a.rounds)).replace('VERSION',a.candidate.name)
 (a.out/'main.cpp').write_text(cpp,encoding='utf-8')
 (a.out/'input.json').write_text(json.dumps({'input':q['init']+''.join(f['input'] for f in frames)+'ENDGAME\n','source':evidence['source'],'source_sha256':evidence['source_sha256'],'verified_events':evidence['physical_events'],'scope':'Original complete observations and actions until choose-only interventions, no earlier candidate decisions. No full-game strength claim.','recorded_state':restored},indent=2),encoding='utf-8')
 print(a.out)
if __name__=='__main__':main()
