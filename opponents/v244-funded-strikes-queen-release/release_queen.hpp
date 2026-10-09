#pragma once
#include "forage.hpp"
namespace release_queen {
using namespace strategy;
inline void apply(const Controller& ct,const Memory& m,forage::Plan& plan){
    if(ct.get_id()<=1 || ct.get_unit_count()<3)return;
    Simulation future{m.body,{},(int)m.body.size()==ct.get_length(),ct.get_length()};
    if(future.body.empty())return;
    if(!plan.action.child_size){
        int steps=0,free=(ct.get_length()+3)/4;
        for(auto d:plan.moves){
            if(!simulate_step(ct,future,d,&m))return; // A planned death already releases this body.
            if(steps++>=free){--future.length;while((int)future.body.size()>future.length)future.body.pop_back();}
        }
    }
    for(const auto& qt:ct.get_tiles()){
        auto q=qt.get_dragon();if(!q||!q->is_head()||q->get_id()>1||q->get_team()!=ct.get_team())continue;
        int available=0,ours=0;bool complete=true;
        for(auto d:Direction::get_direction_list()){
            if(qt.get_edge(d).get_edge_type()==EdgeType::KELP)continue;
            Position n;if(!m.destination(ct,qt.get_position(),d,n)){complete=false;break;}
            auto t=ct.get_tile(n);if(!t){complete=false;break;}
            auto p=t->get_dragon();if(p&&p->get_id()!=ct.get_id())continue;
            bool occupied=std::find(future.body.begin(),future.body.end(),n)!=future.body.end();
            if(!future.complete&&p)occupied=true;
            if(occupied)++ours;else ++available;
        }
        if(!complete || available>0 || ours==0)continue;
        for(auto d:Direction::get_direction_list()){
            Position n;if(!m.destination(ct,ct.get_position(),d,n))continue;
            auto t=ct.get_tile(n);auto p=t?t->get_dragon():nullptr;
            if(p&&p->get_id()==ct.get_id()&&!p->is_head()){
                plan={{d,0},{d},"OCT8 RELEASE_TRAPPED_QUEEN"};return;
            }
        }
    }
}
}
