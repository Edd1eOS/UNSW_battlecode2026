#include "../bot/forage.hpp"

// A fixed observation trace, not a counterfactual live match.
int main() {
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State state;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto plan = forage::choose(ct, memory, state);
        std::cout << "ROUND " << game.get_round_num() << " HEAD " << ct.get_position().x << ',' << ct.get_position().y
                  << " LENGTH " << ct.get_length() << " GOAL " << state.goal
                  << " MOVE ";
        for (auto d : plan.moves) std::cout << d;
        std::cout << " SPLIT " << plan.action.child_size << '\n';
        if (state.goal >= 0) {
            auto field = forage::distances(ct, memory, forage::position(memory,state.goal), true);
            for (auto d : unswbc::Direction::get_direction_list()) {
                strategy::Simulation s{memory.body,{},true,ct.get_length()};
                if (!strategy::simulate_step(ct,s,d,&memory)) continue;
                const auto p=s.body.front();int budget=110;
                auto future=strategy::search_survival(ct,s,0,6,budget,&memory);
                auto e=strategy::evaluate(ct,p,&memory);
                std::cout << d << " distance=" << field[memory.index(p)]
                          << " visits=" << memory.visits(p) << " space=" << e.space
                          << " food=" << s.eaten.size() << " depth=" << future.depth
                          << " uncertain=" << future.uncertain << '\n';
            }
        }
        strategy::remember_action(ct,memory,plan.action,plan.moves,game.get_round_num());
    }
}
