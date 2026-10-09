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
        if(ct.get_id()>1 && ct.get_length()<=8) {
            const unswbc::Tile* queen=nullptr;
            for(const auto& t:ct.get_tiles())if(auto p=t.get_dragon())
                if(p->is_head()&&p->get_id()<=1&&p->get_team()==ct.get_team())queen=&t;
            if(queen){
                int free=0;std::vector<unswbc::Position> own_exits;
                for(auto d:unswbc::Direction::get_direction_list()){
                    if(queen->get_edge(d).get_edge_type()==unswbc::EdgeType::KELP)continue;
                    unswbc::Position p;
                    if(!memory.destination(ct,queen->get_position(),d,p)){++free;continue;}
                    const auto* t=ct.get_tile(p);const auto* part=t?t->get_dragon():nullptr;
                    if(!part)++free;else if(part->get_id()==ct.get_id())own_exits.push_back(p);
                }
                bool opens=false;
                if(!plan.action.child_size){
                    strategy::Simulation future{memory.body,{},static_cast<int>(memory.body.size())==ct.get_length(),ct.get_length()};
                    bool valid=true;for(auto d:plan.moves)if(!strategy::simulate_step(ct,future,d,&memory)){valid=false;break;}
                    if(valid)for(auto p:own_exits)if(std::find(future.body.begin(),future.body.end(),p)==future.body.end())opens=true;
                }
                if(free==0&&!own_exits.empty()&&!opens){
                    for(auto d:unswbc::Direction::get_direction_list()){
                        unswbc::Position p;if(!memory.destination(ct,ct.get_position(),d,p))continue;
                        const auto* t=ct.get_tile(p);auto part=t?t->get_dragon():nullptr;
                        if(part&&part->get_id()==ct.get_id()&&!part->is_head()){
                            plan.action={d,0};plan.moves={d};plan.note="OCT8 OPEN_QUEEN_EXIT";break;
                        }
                    }
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
