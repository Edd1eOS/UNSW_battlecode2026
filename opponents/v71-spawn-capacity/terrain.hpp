#pragma once
#include "strategy.hpp"

namespace terrain {
using namespace strategy;
// Peel terminal branches from the known terrain graph. Unknown boundaries and
// unresolved portals are possible exits, never evidence of a sealed cul-de-sac.
struct EscapeMap {
    std::vector<int> distance;
    static constexpr int unreachable=1000000;
    bool worsens(const Memory& m,Position from,Position to) const {
        if(!m.cell(from) || !m.cell(to)) return false;
        const int a=distance[m.index(from)],b=distance[m.index(to)];
        return a<unreachable && b>a;
    }
};
inline EscapeMap build(const Controller& ct,const Memory& m) {
    const int size=static_cast<int>(m.cells.size());
    std::vector<std::vector<int>> edges(size);
    std::vector<int> degree(size,0);
    std::vector<bool> pinned(size,false),removed(size,false);
    for(int i=0;i<size;++i) {
        if(!m.cells[i].known) {pinned[i]=true;continue;}
        Position p{i%m.width,i/m.width};
        for(auto d:Direction::get_direction_list()) {
            Position n;
            if(!m.destination(ct,p,d,n)) {
                if(m.cells[i].edges[Atlas::direction_index(d)].is_portal()) pinned[i]=true;
                continue;
            }
            if(!m.cell(n)) continue;
            const int j=m.index(n);
            if(!m.cells[j].known) pinned[i]=true;
            if(std::find(edges[i].begin(),edges[i].end(),j)==edges[i].end()) edges[i].push_back(j);
        }
        degree[i]=static_cast<int>(edges[i].size());
    }
    std::queue<int> q;
    for(int i=0;i<size;++i) if(!pinned[i] && degree[i]<=1) {removed[i]=true;q.push(i);}
    while(!q.empty()) {
        const int i=q.front();q.pop();
        for(int j:edges[i]) if(!removed[j] && !pinned[j] && --degree[j]<=1) {removed[j]=true;q.push(j);}
    }
    EscapeMap result;result.distance.assign(size,EscapeMap::unreachable);
    for(int i=0;i<size;++i) if(!removed[i]) {result.distance[i]=0;q.push(i);}
    while(!q.empty()) {
        const int i=q.front();q.pop();
        for(int j:edges[i]) if(result.distance[j]>result.distance[i]+1) {
            result.distance[j]=result.distance[i]+1;q.push(j);
        }
    }
    return result;
}

// A completely known small chamber needs room for the next pearl growth.
// Zero means open/large/uncertain, not a claim that it has no space.
inline int imminent_capacity(const Controller& ct,const Memory& m) {
    std::vector<Position> cells{ct.get_position()}; bool food=false;
    for(std::size_t k=0;k<cells.size();++k) {
        const auto* c=m.cell(cells[k]);if(!c || !c->known) return 0;
        food=food || c->pearl || (c->spawn_round>=m.now && c->spawn_round<=m.now+8);
        for(auto d:Direction::get_direction_list()) {
            Position next;
            if(!m.destination(ct,cells[k],d,next)) {
                if(c->edges[Atlas::direction_index(d)].is_portal()) return 0;
                continue;
            }
            if(!m.cell(next) || !m.cell(next)->known) return 0;
            if(std::find(cells.begin(),cells.end(),next)==cells.end()) {
                cells.push_back(next);if(cells.size()>16) return 0;
            }
        }
    }
    return food?static_cast<int>(cells.size()):0;
}
}
