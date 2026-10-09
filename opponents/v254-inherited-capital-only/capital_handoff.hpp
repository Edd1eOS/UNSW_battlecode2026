#pragma once
#include "strategy.hpp"

namespace capital_handoff {
using namespace strategy;

// Evaluate the reversed child with the retained parent still blocking its two cells.
// Only use the parent's observed state; unseen tail exits do not count as evidence.
inline bool prefer(const Controller& ct,const Memory& m,
                   const std::vector<Direction>& moves,
                   const std::vector<double>& danger,int move_viable) {
    if(ct.get_id()<=1 || ct.get_length()<8 || !ct.can_split(ct.get_length()-2)
       || static_cast<int>(m.body.size())!=ct.get_length() || moves.empty()) return false;
    Simulation moving{m.body,{},true,ct.get_length()};
    bool legal=true;
    for(auto d:moves) if(!simulate_step(ct,moving,d,&m)){legal=false;break;}
    const double current_risk=legal?danger[m.index(moving.body.front())]:100.0;
    if(legal && move_viable>0 && current_risk<0.25) return false;
    const auto tail=m.body.back();
    if(!ct.get_tile(tail)) return false;
    Controller child=ct;
    child.length=ct.get_length()-2;child.head.position=tail;
    for(int i=0;i<2;++i) {
        auto* t=child.get_tile(m.body[i]);
        if(t && t->dragon_part) t->dragon_part->dragon_id=-1;
    }
    Simulation born;born.complete=true;born.length=child.length;
    for(auto it=m.body.rbegin();it!=m.body.rend()-2;++it) born.body.push_back(*it);
    for(auto d:Direction::get_direction_list()) {
        auto after=born;
        if(!simulate_step(child,after,d,&m)) continue;
        const auto risk=danger[m.index(after.body.front())];
        if(risk>0.01 || (legal && move_viable>0 && risk+0.20>=current_risk)) continue;
        int budget=140;
        if(search_survival(child,after,1,6,budget,&m).depth==6) return true;
    }
    return false;
}
}
