#include "planner.hpp"
int main() {
    auto [ct,game]=unswbc::init();
    strategy::Memory memory;planner::State state;
    while(unswbc::update(ct,game)) {
        memory.observe(ct);memory.remember(ct.get_position());
        const auto plan=planner::choose(ct,memory,state);
        ct.set_indicator_string(plan.note);
        if(plan.action.child_size>0)ct.do_split(plan.action.child_size);
        else ct.make_moves(plan.moves);
        if(plan.kind==planner::Kind::UnknownPortal)memory.body.clear();
        else strategy::remember_action(ct,memory,plan.action,plan.moves,game.get_round_num());
        unswbc::end_turn();
    }
}
