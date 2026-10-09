#include "helper.hpp"
#include "strategy.hpp"
#include "forage.hpp"
#include "map_radio.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    forage::State team;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        map_radio::receive(ct,memory);
        memory.remember(ct.get_position());
        auto plan = forage::choose(ct, memory, team);
        if(!plan.action.child_size && !plan.moves.empty()) {
            auto friendly_head=[&](unswbc::Direction d){
                unswbc::Position to;if(!memory.destination(ct,ct.get_position(),d,to))return false;
                const auto* t=ct.get_tile(to);const auto* p=t?t->get_dragon():nullptr;
                return p&&p->get_team()==ct.get_team()&&p->get_id()!=ct.get_id()&&p->is_head();
            };
            if(friendly_head(plan.moves.front())) {
                // A forced loss should not destroy another friendly dragon as well.
                for(auto d:unswbc::Direction::get_direction_list())if(!friendly_head(d)){
                    plan.moves={d};plan.action.direction=d;plan.note="V124 AVOID_FRIENDLY_HEAD";break;
                }
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
        map_radio::send(ct,memory);
        unswbc::end_turn();
    }
}
