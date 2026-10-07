#include "../opponents/generalist-cooperation-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
 auto [ct,game]=init();strategy::Memory memory;planner::State state;
 while(update(ct,game)) {
  planner::observe(ct,memory,state);memory.remember(ct.get_position());
  // Replay state is built only by the unchanged V5 policy. Probes use copies
  // and receive no historical packet after their divergent action.
  auto historical=planner::choose(ct,memory,state,false);
  std::cout<<"BASE "<<game.get_round_num()<<" selected=";for(auto d:historical.moves)std::cout<<d.value;
  std::cout<<" child="<<historical.action.child_size<<"\n";
  if((ct.get_id()==11&&game.get_round_num()==182)||(ct.get_id()==1&&game.get_round_num()==146)) {
   auto probe_memory=memory;auto probe_state=state;auto probe=planner::choose(ct,probe_memory,probe_state);
   std::cout<<"PROBE "<<game.get_round_num()<<" ";for(auto d:probe.moves)std::cout<<d.value;
   std::cout<<" child="<<probe.action.child_size<<" "<<probe.note<<std::endl;
   if(ct.get_id()==11) {
#ifndef COOPERATION_DISABLE_EGRESS
    cooperation::Model model(ct,memory);std::cout<<"RESCUE original="<<model.preserves_all(memory.body)<<" queens="<<model.queens.size()<<std::endl;
    auto parent=planner::initial(ct,memory);strategy::Simulation child;child.complete=true;child.length=2;
    child.body={memory.body.back(),memory.body[memory.body.size()-2]};parent.length-=2;parent.body.resize(parent.length);
    std::vector<Position> blocked(parent.body.begin(),parent.body.end());Direction child_dir=ct.get_dir();
    std::cout<<"FACING "<<planner::child_facing(ct,memory,child,child_dir)<<" "<<child_dir.value<<std::endl;
    for(auto d:Direction::get_direction_list()) {Position to;bool resolved=memory.destination(ct,child.body.front(),d,to);auto next=child;
      bool legal=resolved&&ct.get_tile(to)&&planner::step(ct,memory,next,d,false,blocked);std::vector<Position> after(next.body.begin(),next.body.end());
      std::cout<<"CHILD "<<d.value<<" resolved="<<resolved<<" legal="<<legal<<" preserve="<<model.preserves_all(parent.body,after)<<std::endl;}
    assert(probe.kind==planner::Kind::Split&&probe.action.child_size==2);
    // Reverse remains forbidden and no legal child exit means no proposal.
    auto blocked_memory=memory;auto blocked_state=state;
    const Position tail=memory.body.back();auto original_vision=ct.vision;
    for(auto d:Direction::get_direction_list())if(d!=Direction(Direction::SOUTH)) {
      ct.get_tile(tail)->get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::KELP,-1};
      if(auto* t=ct.get_tile(tail.add_dir(d)))t->get_edge(d.get_opposite())=ct.get_tile(tail)->get_edge(d);
    }
    blocked_memory.observe_map(ct,182);auto no_child=planner::choose(ct,blocked_memory,blocked_state);
    assert(no_child.kind!=planner::Kind::Split||no_child.note.find("team_egress_split=1")==std::string::npos);
    ct.vision=std::move(original_vision);
#else
    assert(probe.action.child_size==historical.action.child_size&&probe.moves==historical.moves);
#endif
   } else {
#ifndef COOPERATION_DISABLE_ARRIVAL
    assert(probe.kind==planner::Kind::Move&&!probe.moves.empty());
    assert(probe.moves.front()!=Direction(Direction::EAST));
    assert(probe.note.find("depth=8")!=std::string::npos);
#else
    assert(probe.moves==historical.moves);
#endif
   }
  }
  planner::remember(ct,memory,state,historical,game.get_round_num());
 }
}
