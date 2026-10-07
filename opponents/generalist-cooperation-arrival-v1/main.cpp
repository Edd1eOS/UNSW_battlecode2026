#define COOPERATION_DISABLE_EGRESS
#include "planner.hpp"
int main() {
    auto [ct,game]=unswbc::init();
    strategy::Memory memory;planner::State state;
    while(unswbc::update(ct,game)) {
        planner::observe(ct,memory,state);memory.remember(ct.get_position());
        const auto plan=planner::choose(ct,memory,state);
        ct.set_indicator_string(plan.note);
        if(plan.action.child_size>0)ct.do_split(plan.action.child_size);
        else ct.make_moves(plan.moves);
        planner::remember(ct,memory,state,plan,game.get_round_num());
        unswbc::end_turn();
    }
}
