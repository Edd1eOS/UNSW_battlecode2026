#include "helper.hpp"
#include "baseline_human.hpp"
#include "human.hpp"
int main(){
 auto [ct,game]=unswbc::init(); strategy::Memory memory;
 baseline::State old_state; human::State new_state;
 while(unswbc::update(ct,game)){
  memory.observe(ct);memory.remember(ct.get_position());
  human::Plan plan{{ct.get_dir(),0},{},""};
  if(game.get_round_num()<282){
   auto old=baseline::choose(ct,memory,old_state);plan={old.action,old.moves,old.note};
  } else {
   if(game.get_round_num()==282){
    new_state.goal=old_state.goal;new_state.last_portal=old_state.last_portal;
    new_state.queen_brood_done=old_state.queen_brood_done;
   }
   plan=human::choose(ct,memory,new_state);
  }
  ct.set_indicator_string(plan.note);
  if(plan.action.child_size){
   ct.do_split(plan.action.child_size);
   if(ct.get_id()<=1&&plan.note.find(" FLOOD ")!=std::string::npos){
    if(game.get_round_num()<282)old_state.queen_brood_done=true;
    else new_state.queen_brood_done=true;
   }
  }else ct.make_moves(plan.moves);
  strategy::remember_action(ct,memory,plan.action,plan.moves,game.get_round_num());
  unswbc::end_turn();
 }
}
