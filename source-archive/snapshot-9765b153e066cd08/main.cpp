#include "helper.hpp"
#include "strategy.hpp"
#include "forage.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State team;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto plan = forage::choose(ct, memory, team);
        const auto decision = plan.action;
        if(ct.get_id()<=1) {
            auto exits=terrain::build(ct,memory); auto danger=forage::danger_map(ct,memory);
            for(auto d:unswbc::Direction::get_direction_list()) {
                strategy::Simulation sim{memory.body,{},static_cast<int>(memory.body.size())==ct.get_length(),ct.get_length()};
                bool legal=strategy::simulate_step(ct,sim,d,&memory);
                if(!legal) {ct.log("DIAG",char(d.value),"illegal");continue;}
                auto end=sim.body.front();int budget=220;
                auto future=strategy::search_survival(ct,sim,0,8,budget,&memory);
                ct.log("DIAG",char(d.value),"legal","peeled",exits.worsens(memory,ct.get_position(),end),"depth",future.depth,"unknown",future.uncertain,"danger",danger[memory.index(end)]);
            }
        }
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
