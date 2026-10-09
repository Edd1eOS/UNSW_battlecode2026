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
        if(ct.get_id()<=1 && !memory.body.empty()) {
            auto ray=plan.moves.empty()?ct.get_dir():plan.moves.back();
            auto origin=memory.body.front(),at=origin;bool valid=true;
            for(int step=0;step<7;++step){
                auto t=ct.get_tile(at);if(!t)break;
                if(t->get_edge(ray).is_portal()){valid=false;break;}
                unswbc::Position next;if(!memory.destination(ct,at,ray,next))break;
                if(std::find(memory.body.begin(),memory.body.end(),next)!=memory.body.end()){valid=false;break;}
                at=next;
            }
            team.echo_dir=valid?strategy::Atlas::direction_index(ray):-1;
            team.echo_round=memory.now;team.echo_position=memory.index(origin);
            ct.send_sonar(ray,0);
        }
        unswbc::end_turn();
    }
}
