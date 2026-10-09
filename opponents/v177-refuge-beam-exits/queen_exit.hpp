#pragma once
#include "forage.hpp"
namespace queen_exit {
using namespace strategy;
inline bool seals(const Controller& ct,const Memory& m,const std::vector<Direction>& moves){
    if(ct.get_id()<=1 || moves.empty())return false;
    Simulation future{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
    int step=0,free=(ct.get_length()+3)/4;
    for(auto d:moves){
        if(!simulate_step(ct,future,d,&m))return false; // Its death frees its body.
        if(step++>=free){--future.length;while((int)future.body.size()>future.length)future.body.pop_back();}
    }
    for(const auto& qt:ct.get_tiles()){
        auto q=qt.get_dragon();if(!q||!q->is_head()||q->get_id()>1||q->get_team()!=ct.get_team())continue;
        int before=0,after=0;bool complete=true;
        for(auto d:Direction::get_direction_list()){
            if(qt.get_edge(d).get_edge_type()==unswbc::EdgeType::KELP)continue;
            Position n;if(!m.destination(ct,qt.get_position(),d,n)){complete=false;break;}
            const auto* t=ct.get_tile(n);if(!t){complete=false;break;}
            const auto* p=t->get_dragon();if(!p)++before;
            bool occupied=p&&p->get_id()!=ct.get_id();
            occupied=occupied||std::find(future.body.begin(),future.body.end(),n)!=future.body.end();
            if(!occupied)++after;
        }
        if(complete&&before>0&&after==0)return true;
    }
    return false;
}
inline void apply(const Controller& ct,const Memory& m,forage::Plan& plan){
    if(plan.action.child_size || !seals(ct,m,plan.moves))return;
    for(auto d:Direction::get_direction_list()){
        Simulation s{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
        if(simulate_step(ct,s,d,&m) && !seals(ct,m,{d})){
            plan={{d,0},{d},"OCT8 KEEP_QUEEN_EXIT"};return;
        }
    }
    // No legal moving alternative: dying alone leaves the Queen's last exit open.
    for(auto d:Direction::get_direction_list()){
        Position n;if(!m.destination(ct,ct.get_position(),d,n))continue;
        const auto* t=ct.get_tile(n);auto p=t?t->get_dragon():nullptr;
        if(p&&p->get_id()==ct.get_id()&&!p->is_head()){
            plan={{d,0},{d},"OCT8 YIELD_QUEEN_EXIT"};return;
        }
    }
}
}
