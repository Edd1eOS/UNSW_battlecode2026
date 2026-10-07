#pragma once
#include "strategy.hpp"

// An unknown exit is an information opportunity, never food or proven safety.
// This narrowly changes dry harvest workers; Queen/reserve/last keep V5 policy.
namespace exploration {
using namespace strategy;
struct Budget { int next_allowed=0, attempts=0; };
struct PortalOpportunity { Direction direction; int portal_id; };
inline bool eligible(const Controller& ct,const Memory& m,bool reserve,
                     int last_food,const Budget& budget) {
    if(ct.get_id()<=1 || ct.get_unit_count()<=1 || reserve
       || static_cast<int>(m.body.size())!=ct.get_length()
       || m.now-last_food<24 || m.now<budget.next_allowed)return false;
    // Even a headless visible enemy body can become a same-round split head.
    // Do not override the existing risk pipeline in such a contested window.
    for(const auto& t:ct.get_tiles()) {
        const auto* part=t.get_dragon();
        if(part&&part->get_team()!=ct.get_team())return false;
    }
    return true;
}
inline std::vector<PortalOpportunity> opportunities(const Controller& ct,const Memory& m) {
    std::vector<PortalOpportunity> result;
    const auto* here=ct.get_tile(ct.get_position());if(!here)return result;
    for(auto d:Direction::get_direction_list()) {
        if(ct.get_length()>=2&&d==ct.get_dir().get_opposite())continue;
        const auto& edge=here->get_edge(d);Position to;
        if(!edge.is_portal() || m.destination(ct,ct.get_position(),d,to))continue;
        const int id=edge.get_portal_id();
        if(std::any_of(result.begin(),result.end(),[&](const PortalOpportunity& x){return x.portal_id==id;}))continue;
        result.push_back({d,id});
    }
    return result;
}
inline void spend(Budget& budget,int now) {
    budget.next_allowed=now+24;++budget.attempts;
}
}
