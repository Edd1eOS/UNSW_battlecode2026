#include "helper.hpp"
#include "strategy.hpp"
#include "forage.hpp"
#include "queen.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State team;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        auto plan = ct.get_id()<=1 ? queen120::choose(ct, memory, team) : forage::choose(ct, memory, team);
        // A trapped worker must never take the Queen down with its fallback move.
        if(ct.get_id()>1 && !plan.action.child_size && !plan.moves.empty()) {
            auto hits_queen=[&](unswbc::Direction d){
                unswbc::Position to;if(!memory.destination(ct,ct.get_position(),d,to))return false;
                const auto* t=ct.get_tile(to);const auto* p=t?t->get_dragon():nullptr;
                return p&&p->get_team()==ct.get_team()&&p->get_id()<=1&&p->is_head();
            };
            if(hits_queen(plan.moves.front()))for(auto d:unswbc::Direction::get_direction_list())if(!hits_queen(d)){
                plan.moves={d};plan.action.direction=d;plan.note="V121 NO_FRIENDLY_QUEEN_CONTACT";break;
            }
        }
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
