#include "helper.hpp"
#include "strategy.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto decision = strategy::choose_action(ct, memory, game.get_round_num());
        if (decision.child_size > 0) {
            ct.do_split(decision.child_size);
            strategy::remember_action(ct, memory, decision, {}, game.get_round_num());
        } else {
            const auto moves = strategy::plan_moves(ct, memory, decision.direction);
            ct.make_moves(moves);
            strategy::remember_action(ct, memory, decision, moves, game.get_round_num());
        }
        unswbc::end_turn();
    }
}
