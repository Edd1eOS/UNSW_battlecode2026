#include "helper.hpp"
#include "strategy.hpp"
#include "cooperation.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    cooperation::Memory team;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto plan = cooperation::choose_turn(ct, memory, team, game.get_round_num(), {true,false,true});
        const auto decision = plan.action;
        if (!plan.telemetry.empty()) ct.set_indicator_string(plan.telemetry);
        if (plan.sonar) ct.send_sonar(plan.sonar->first, plan.sonar->second);
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
