#include "helper.hpp"
#include "strategy.hpp"
#include "forage.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State team;
    while (unswbc::update(ct, game)) {
        if(game.get_round_num()>=298) std::cout << "LOG BEFORE len=" << ct.get_length() << " old=" << team.old_length << " growth=" << team.last_growth << " goal=" << team.goal << "\n";
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto plan = forage::choose(ct, memory, team);
        if(game.get_round_num()>=298) std::cout << "LOG AFTER len=" << ct.get_length() << " old=" << team.old_length << " growth=" << team.last_growth << " goal=" << team.goal << "\n";
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
