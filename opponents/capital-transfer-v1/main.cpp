#include "planner.hpp"
#include "capital_transfer.hpp"
int main() {
    auto [ct,game]=unswbc::init();
    strategy::Memory memory;planner::State state;transfer::State delivery;
    while(unswbc::update(ct,game)) {
        planner::observe(ct,memory,state);memory.remember(ct.get_position());
        auto plan=planner::choose(ct,memory,state);
        const auto cooperation=transfer::prepare(ct,memory,delivery,plan);
        ct.set_indicator_string(plan.note);
        if(plan.action.child_size>0)ct.do_split(plan.action.child_size);
        else ct.make_moves(plan.moves);
        if(cooperation.sonar)ct.send_sonar(cooperation.sonar->first,cooperation.sonar->second);
        if(!cooperation.release)planner::remember(ct,memory,state,plan,game.get_round_num());
        unswbc::end_turn();
    }
}
