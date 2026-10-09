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
        if(ct.get_id()>1 && ct.get_length()<=4 && ct.get_unit_count()>=8 && memory.now>=300) {
            bool enemy=false;int recipient=-1,value=-1;
            for(const auto& t:ct.get_tiles())if(auto part=t.get_dragon()) {
                if(part->get_team()!=ct.get_team())enemy=true;
                if(part->get_team()!=ct.get_team() || !part->is_head() || part->get_id()>=ct.get_id())continue;
                bool adjacent=false;for(auto d:unswbc::Direction::get_direction_list()){
                    unswbc::Position n;if(memory.destination(ct,t.get_position(),d,n)&&n==ct.get_position())adjacent=true;
                }
                if(!adjacent)continue;
                int length=0;for(const auto& tile:ct.get_tiles())if(tile.get_dragon()&&tile.get_dragon()->get_id()==part->get_id())++length;
                int merit=part->get_id()<=1?1000:(length>=6?length:0);
                if(merit>value&&merit>0){value=merit;recipient=part->get_id();}
            }
            if(!enemy && recipient>=0)for(auto d:unswbc::Direction::get_direction_list()){
                unswbc::Position n;if(!memory.destination(ct,ct.get_position(),d,n))continue;
                auto t=ct.get_tile(n);auto part=t?t->get_dragon():nullptr;
                if(part&&part->get_id()==ct.get_id()&&!part->is_head()){
                    plan={{d,0},{d},"OCT8 ENDGAME_FEED recipient="+std::to_string(recipient)};break;
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
