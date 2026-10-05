#include "proxy.hpp"

int main() {
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State state;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto plan = short_swarm_proxy::choose(ct, memory, state);
        ct.set_indicator_string(plan.note);
        if (plan.action.child_size > 0) ct.do_split(plan.action.child_size);
        else ct.make_moves(plan.moves);
        strategy::remember_action(ct, memory, plan.action, plan.moves, game.get_round_num());
        unswbc::end_turn();
    }
}
