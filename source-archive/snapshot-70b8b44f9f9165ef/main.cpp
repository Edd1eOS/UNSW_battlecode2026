#include "helper.hpp"
#include "human.hpp"
int main(){
    auto [ct,game]=unswbc::init();strategy::Memory memory;human::State state;
    while(unswbc::update(ct,game)){
        memory.observe(ct);memory.remember(ct.get_position());
        auto plan=human::choose(ct,memory,state);ct.set_indicator_string(plan.note);
        if(plan.action.child_size){
            ct.do_split(plan.action.child_size);
            // Mark only the ordinary brood action actually emitted this turn.
            // Emergency tail handoff remains independent of this lifetime cap.
            if(ct.get_id()<=1&&plan.note.rfind("V268 FLOOD ",0)==0)
                state.queen_brood_done=true;
        }
        else ct.make_moves(plan.moves);
        strategy::remember_action(ct,memory,plan.action,plan.moves,game.get_round_num());
        unswbc::end_turn();
    }
}
