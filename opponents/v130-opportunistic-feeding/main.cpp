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
        auto plan = forage::choose(ct, memory, team);
        if(ct.get_id()>1 && ct.get_length()<=6 && ct.get_unit_count()>=6 && memory.now>=100) {
            bool enemy=false;const unswbc::Tile* queen=nullptr;
            for(const auto& t:ct.get_tiles())if(auto p=t.get_dragon()){
                if(p->get_team()!=ct.get_team())enemy=true;
                else if(p->is_head()&&p->get_id()<=1)queen=&t;
            }
            bool reachable=false;
            if(queen)for(auto d:unswbc::Direction::get_direction_list()){
                unswbc::Position to;if(memory.destination(ct,queen->get_position(),d,to)&&to==ct.get_position())reachable=true;
            }
            if(reachable&&!enemy)for(auto d:unswbc::Direction::get_direction_list()){
                unswbc::Position to;if(!memory.destination(ct,ct.get_position(),d,to))continue;
                const auto* t=ct.get_tile(to);auto p=t?t->get_dragon():nullptr;
                if(p&&p->get_id()==ct.get_id()&&!p->is_head()){
                    plan.action={d,0};plan.moves={d};plan.note="V130 QUEEN_FEED";break;
                }
            }
        }
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
        unswbc::end_turn();
    }
}
