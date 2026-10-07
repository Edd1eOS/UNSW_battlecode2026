#pragma once
#include "strategy.hpp"

namespace topology {
using namespace strategy;
// Each state is a remembered directed terrain edge (previous -> current).
// Future moves may not return to the old neck. Other bodies and pearls are
// deliberately absent: this is a necessary terrain condition, not survival.
struct Evidence {
    bool known=false, cycle_possible=false, unknown_reachable=true;
    int remaining=0;
    bool finite() const {return known&&!cycle_possible&&!unknown_reachable;}
};
struct Kernel {
    std::vector<int> destination, remaining;
    std::vector<unsigned char> valid, cycle, unknown;
    bool available=false;
    static constexpr int blocked=-1,unresolved=-2;
    Evidence at(const Memory& m,const Simulation& s) const {
        if(!available||s.body.size()<2||!m.cell(s.body[0])||!m.cell(s.body[1]))return {};
        int a=m.index(s.body[1]),b=m.index(s.body[0]);
        for(int d=0;d<4;++d){int state=4*a+d;
            if(valid[state]&&destination[state]==b)return {true,cycle[state]!=0,unknown[state]!=0,remaining[state]};}
        return {};
    }
};
inline int remembered_destination(const Memory& m,Position p,Direction d,int edge_index) {
    const auto* c=m.cell(p);if(!c||!c->known)return Kernel::unresolved;
    const auto& edge=c->edges[edge_index];
    if(edge.get_edge_type()==EdgeType::KELP)return Kernel::blocked;
    if(!edge.is_portal())return m.index(p.add_dir(d));
    auto it=m.portals.find(edge.get_portal_id());
    if(it==m.portals.end()||it->second.size()!=2)return Kernel::unresolved;
    const auto entry=Atlas::mouth(p,d);const auto& pair=it->second;
    int which=pair[0].base==entry.base&&pair[0].horizontal==entry.horizontal?0:1;
    if(pair[which].base!=entry.base||pair[which].horizontal!=entry.horizontal)return Kernel::unresolved;
    const auto& other=pair[1-which];if(other.horizontal!=entry.horizontal)return Kernel::unresolved;
    Position out=other.base;
    if(d==Direction(Direction::EAST)||d==Direction(Direction::SOUTH))out=out.add_dir(d);
    return m.cell(out)?m.index(out):Kernel::unresolved;
}
inline Kernel build(const Memory& m) {
    Kernel k;const int cells=static_cast<int>(m.cells.size());
    // Unsupported large history remains unknown; never truncate into a seal.
    if(cells<=0||cells>8192)return k;
    const int count=4*cells;
    k.destination.assign(count,Kernel::blocked);k.remaining.assign(count,0);
    k.valid.assign(count,0);k.cycle.assign(count,0);k.unknown.assign(count,0);
    // Flat reverse adjacency avoids a heap allocation for each terrain state.
    std::vector<int> first_reverse(count,-1),reverse_from,reverse_next;
    reverse_from.reserve(3*count);reverse_next.reserve(3*count);
    std::vector<int> outdegree(count,0);std::vector<unsigned char> boundary(count,0);
    const auto dirs=Direction::get_direction_list();
    for(int i=0;i<cells;++i)if(m.cells[i].known)for(int d=0;d<4;++d){
        int target=remembered_destination(m,Position{i%m.width,i/m.width},dirs[d],d);
        if(target==i)target=Kernel::blocked; // A self-loop hits the old head.
        k.destination[4*i+d]=target;k.valid[4*i+d]=target!=Kernel::blocked;
    }
    for(int v=0;v<count;++v)if(k.valid[v]) {
        const int previous=v/4,current=k.destination[v];
        if(current==Kernel::unresolved||!m.cells[current].known){boundary[v]=1;continue;}
        for(int d=0;d<4;++d){int next=4*current+d,target=k.destination[next];
            if(!k.valid[next]||target==previous||target==current)continue;
            reverse_from.push_back(v);reverse_next.push_back(first_reverse[next]);
            first_reverse[next]=static_cast<int>(reverse_from.size())-1;++outdegree[v];
        }
    }
    // Reverse reachability distinguishes an unseen outlet from a known cycle.
    std::queue<int> q;
    for(int v=0;v<count;++v)if(boundary[v]){k.unknown[v]=1;q.push(v);}
    while(!q.empty()){int v=q.front();q.pop();for(int edge=first_reverse[v];edge>=0;edge=reverse_next[edge]){
        int before=reverse_from[edge];if(!k.unknown[before]){k.unknown[before]=1;q.push(before);}}}
    // Peel every sink, including unknown terminal nodes. The nodes left can
    // reach an actual cycle in the known non-backtracking terrain graph.
    std::vector<unsigned char> removed(count,0);
    for(int v=0;v<count;++v)if(k.valid[v]&&outdegree[v]==0){removed[v]=1;q.push(v);}
    while(!q.empty()){int v=q.front();q.pop();for(int edge=first_reverse[v];edge>=0;edge=reverse_next[edge]){
        int before=reverse_from[edge];
        k.remaining[before]=std::max(k.remaining[before],k.remaining[v]+1);
        if(--outdegree[before]==0){removed[before]=1;q.push(before);}}}
    for(int v=0;v<count;++v)k.cycle[v]=k.valid[v]&&!removed[v];
    k.available=true;return k;
}
}
