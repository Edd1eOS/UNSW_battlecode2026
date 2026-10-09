#pragma once
#include "strategy.hpp"
namespace tail_route {
using namespace strategy;
inline bool connected(const Controller& ct,const Memory& m,const Simulation& s){
    if(!s.complete || s.body.size()<4)return false;
    const auto target=s.body.back();if(!ct.get_tile(target))return false;
    std::vector<int> dist(m.cells.size(),-1),dry(m.cells.size(),0);
    std::vector<bool> blocked(m.cells.size(),false);
    for(int i=1;i+1<(int)s.body.size();++i)blocked[m.index(s.body[i])]=true;
    std::queue<Position> q;q.push(s.body.front());dist[m.index(s.body.front())]=0;
    while(!q.empty()){
        auto p=q.front();q.pop();
        for(auto d:Direction::get_direction_list()){
            Position n;if(!m.destination(ct,p,d,n) || !m.cell(n))continue;
            const auto* t=ct.get_tile(n);if(!t || blocked[m.index(n)])continue;
            const auto* part=t->get_dragon();if(part&&part->get_id()!=ct.get_id())continue;
            const int a=m.index(p),b=m.index(n);
            if(n==target){if(dist[a]>=1&&dry[a])return true;continue;}
            if(dist[b]>=0)continue;
            bool food=t->has_pearl() && std::find(s.eaten.begin(),s.eaten.end(),n)==s.eaten.end();
            dist[b]=dist[a]+1;dry[b]=dry[a]||!food;q.push(n);
        }
    }
    return false;
}
}
