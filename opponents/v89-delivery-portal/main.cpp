#include "helper.hpp"
#include "strategy.hpp"
#include "forage.hpp"
#include "cooperation.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State team;
    cooperation::Memory delivery;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        auto plan = forage::choose(ct, memory, team);
        cooperation::Plan base; base.action=plan.action; base.moves=plan.moves;
        const auto handoff=cooperation::choose_turn(ct,memory,delivery,game.get_round_num(),{false,false,true},&base,team.collector && ct.get_length()>=4);
        plan.action=handoff.action;plan.moves=handoff.moves;
        if(handoff.sonar) ct.send_sonar(handoff.sonar->first,handoff.sonar->second);
        if(!handoff.telemetry.empty()) plan.note+=" "+handoff.telemetry;
        const auto decision = plan.action;
        if (!plan.note.empty()) ct.set_indicator_string(plan.note);
        if (decision.child_size > 0) {
            ct.do_split(decision.child_size);
            strategy::remember_action(ct, memory, decision, {}, game.get_round_num());
        } else {
            const auto& moves = plan.moves;
            ct.make_moves(moves);
            strategy::remember_action(ct, memory, decision, moves, game.get_round_num());
        }
        unswbc::end_turn();
    }
}
