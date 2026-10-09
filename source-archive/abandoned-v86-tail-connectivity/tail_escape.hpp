#pragma once
#include "strategy.hpp"
namespace strategy {
struct TailRoute { bool connected=false,uncertain=false;int space=0; };
inline TailRoute tail_route(const Controller& ct,const Memory& m,const Simulation& s) {
    TailRoute r;if(!s.complete || s.body.empty()){r.uncertain=true;return r;}
    std::vector<Position> seen{s.body.front()};
    for(std::size_t k=0;k<seen.size();++k) {
        if(k>=64){r.uncertain=true;break;}
        const auto* from=ct.get_tile(seen[k]);if(!from){r.uncertain=true;continue;}
        ++r.space;
        for(auto d:Direction::get_direction_list()) {
            Position n;if(!m.destination(ct,seen[k],d,n)) {if(from->get_edge(d).is_portal())r.uncertain=true;continue;}
            if(std::find(seen.begin(),seen.end(),n)!=seen.end())continue;
            const auto* tile=ct.get_tile(n);if(!tile){r.uncertain=true;continue;}
            if(tile->get_dragon() && tile->get_dragon()->get_id()!=ct.get_id())continue;
            if(n==s.body.back()){r.connected=true;return r;}
            if(std::find(s.body.begin(),s.body.end(),n)!=s.body.end())continue;
            seen.push_back(n);
        }
    }
    return r;
}
}
