#pragma once
#include "strategy.hpp"
#include <cmath>

namespace foraging {
using namespace unswbc;
// A discounted opportunity field, not a predicted or executed food ledger.
// Geometry uses observed edges (including resolved portals), never Manhattan
// shortcuts. Current foreign bodies block the graph; own-body release is only
// optimistic guidance and remains subject to planner's timed body simulation.
struct Source {
    int index=0;
    double weight=0;
    std::vector<int> distance;
};
struct Field {
    int start=0,work=0;
    bool exhausted=false;
    std::vector<Source> sources;
    double potential(int at,const std::vector<Position>& eaten,int width,int free) const {
        double total=0;
        for(const auto& source:sources) {
            bool consumed=false;
            for(auto p:eaten)if(p.y*width+p.x==source.index){consumed=true;break;}
            if(consumed||at<0||at>=static_cast<int>(source.distance.size()))continue;
            const int d=source.distance[at];
            if(d<0||d>16)continue;
            const double turns=static_cast<double>(d)/std::max(1,free);
            total+=source.weight/std::pow(1+0.35*turns,2);
        }
        return total;
    }
    double progress(int at,const std::vector<Position>& eaten,int width,int free)const {
        // Eaten cells are removed from BOTH endpoints: current food is already
        // rewarded by actual simulation and must not be rewarded a second time.
        const double delta=potential(at,eaten,width,free)-potential(start,eaten,width,free);
        return std::max(-70.0,std::min(70.0,35*delta));
    }
};
inline Field build(const Controller& ct,const strategy::Memory& m) {
    Field f;f.start=m.index(ct.get_position());
    const int size=static_cast<int>(m.cells.size());
    std::vector<std::vector<int>> reverse(size);
    std::vector<int> reached(size,-1);std::queue<int> q;
    reached[f.start]=0;q.push(f.start);
    std::vector<std::pair<double,int>> targets;
    std::vector<double> weights(size,0);
    const int free=std::max(1,(ct.get_length()+3)/4);
    int budget=2048;
    while(!q.empty()&&budget-->0) {
        int at=q.front();q.pop();++f.work;
        Position p{at%m.width,at/m.width};const auto& c=m.cells[at];
        if(!c.known)continue;
        const auto* tile=ct.get_tile(p);
        const auto* part=tile?tile->get_dragon():nullptr;
        if(part&&part->get_id()!=ct.get_id())continue;
        double weight=0;
        if(tile&&tile->has_pearl())weight=1;
        else if(!tile&&c.pearl&&m.now-c.seen<=10)
            weight=0.45*(11-std::max(0,m.now-c.seen))/11.0;
        else if(c.spawn_round>=m.now&&c.spawn_round<=m.now+8) {
            const double arrival=static_cast<double>(reached[at])/free;
            weight=0.20/(1+std::abs(c.spawn_round-m.now-arrival));
        }
        if(weight>0) {
            weights[at]=weight;
            targets.push_back({weight/(1+0.15*reached[at]),at});
        }
        for(auto d:Direction::get_direction_list()) {
            Position to;if(!m.destination(ct,p,d,to)||!m.cell(to))continue;
            const int next=m.index(to);const auto* live=ct.get_tile(to);
            const auto* occupied=live?live->get_dragon():nullptr;
            if(occupied&&occupied->get_id()!=ct.get_id())continue;
            reverse[next].push_back(at);
            if(reached[next]<0){reached[next]=reached[at]+1;q.push(next);}
        }
    }
    f.exhausted=!q.empty();
    std::stable_sort(targets.begin(),targets.end(),[](const auto& a,const auto& b){return a.first>b.first;});
    if(targets.size()>16)targets.resize(16);
    for(auto target:targets) {
        Source s;s.index=target.second;s.weight=weights[s.index];s.distance.assign(size,-1);
        s.distance[s.index]=0;std::queue<int> pending;pending.push(s.index);
        while(!pending.empty()) {
            int at=pending.front();pending.pop();++f.work;
            if(s.distance[at]>=16)continue;
            for(int before:reverse[at])if(s.distance[before]<0) {
                s.distance[before]=s.distance[at]+1;pending.push(before);
            }
        }
        f.sources.push_back(std::move(s));
    }
    return f;
}
} // namespace foraging
