#pragma once
#include "strategy.hpp"

namespace resource_priority {
using namespace strategy;
struct Ally {int id;Position head;int length_lower;};
struct Field {
    std::vector<int> opportunity_cost;
    int beneficiary=-1,marked=0;
    int cost(const Memory& m,const Simulation& s) const {
        int sum=0;for(auto p:s.eaten)if(m.cell(p)&&m.index(p)<static_cast<int>(opportunity_cost.size()))
            sum+=opportunity_cost[m.index(p)];
        return sum;
    }
};
inline Field build(const Controller& ct,const Memory& m,const std::vector<Ally>& allies,
                   const std::vector<bool>& imminent) {
    Field field;if(ct.get_id()<=1)return field;
    Ally selected{-1,{},0};
    for(const auto& ally:allies){
        if(ally.id==ct.get_id())continue;
        if(ally.id<=1){selected=ally;break;}
        if(ally.length_lower>=8&&ally.length_lower>ct.get_length()
           &&(selected.id<0||ally.length_lower>selected.length_lower
              ||(ally.length_lower==selected.length_lower&&ally.id<selected.id)))selected=ally;
    }
    if(selected.id<0||(m.now>=499&&selected.id<ct.get_id()))return field;
    field.beneficiary=selected.id;field.opportunity_cost.assign(m.cells.size(),0);
    const int quota=std::min(4,std::max(1,(selected.length_lower+3)/4));
    const int value=selected.id<=1?65:45;
    std::vector<int> distance(m.cells.size(),-1);std::queue<Position> q;
    q.push(selected.head);distance[m.index(selected.head)]=0;
    while(!q.empty()){
        auto at=q.front();q.pop();int depth=distance[m.index(at)];
        if(depth>=quota)continue;
        for(auto direction:Direction::get_direction_list()){
            Position to;if(!m.destination(ct,at,direction,to)||!m.cell(to))continue;
            int i=m.index(to);if(distance[i]>=0)continue;
            const auto* live=ct.get_tile(to);
            // No claim on unseen pearls or routes through currently occupied cells.
            if(!live||live->get_dragon()||(i<static_cast<int>(imminent.size())&&imminent[i]))continue;
            distance[i]=depth+1;q.push(to);
            if(live->has_pearl()){field.opportunity_cost[i]=value;++field.marked;}
        }
    }
    return field;
}
}
