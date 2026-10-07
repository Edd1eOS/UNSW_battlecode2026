#pragma once
#include "strategy.hpp"

// Population is a flow of local opportunities, not a global target count.
// All claims use this dragon's observation. A champion is regional, not a
// fabricated globally longest dragon. Leases expire when a peer disappears.
namespace colony {
using namespace strategy;
struct Lease { int dominant_id=-1, dominant_seen=-1000; bool champion=false; };
inline int visible_length(const Controller& ct,int id) {
    int n=0;for(const auto& t:ct.get_tiles())if(t.get_dragon()&&t.get_dragon()->get_id()==id)++n;
    return n; // A lower bound, never an inferred total length.
}
inline void update(const Controller& ct,int now,Lease& lease) {
    bool dominated=false;
    for(const auto& t:ct.get_tiles()) {
        auto* p=t.get_dragon();
        if(!p||!p->is_head()||p->get_id()<=1||p->get_id()==ct.get_id()||p->get_team()!=ct.get_team())continue;
        const int length=visible_length(ct,p->get_id());
        if(length>ct.get_length()||(length==ct.get_length()&&p->get_id()<ct.get_id())) {
            dominated=true;lease.dominant_id=p->get_id();lease.dominant_seen=now;
        }
    }
    if(!dominated&&now-lease.dominant_seen>6)lease.dominant_id=-1;
    lease.champion=ct.get_id()>1&&ct.get_length()>=8&&lease.dominant_id<0;
}
struct Opportunity { int room=0,food=0,frontier=0,heads=0; };
inline Opportunity opportunity(const Controller& ct,const Memory& m,const Simulation& child,
                               const std::vector<Position>& parent) {
    Opportunity out;
    std::vector<Position> seen{child.body.front()};std::queue<std::pair<Position,int>> q;
    q.push({child.body.front(),0});
    while(!q.empty()) {
        auto [at,depth]=q.front();q.pop();++out.room;
        const auto* tile=ct.get_tile(at);if(!tile)continue;
        if(tile->has_pearl())++out.food;
        if(depth>=4)continue;
        for(auto d:Direction::get_direction_list()) {
            Position to;if(!m.destination(ct,at,d,to))continue;
            if(std::find(parent.begin(),parent.end(),to)!=parent.end())continue;
            if(std::find(child.body.begin()+1,child.body.end(),to)!=child.body.end())continue;
            const auto* next=ct.get_tile(to);
            if(!next){++out.frontier;continue;}
            if(const auto* p=next->get_dragon()) {
                if(p->get_id()!=ct.get_id())continue;
            }
            if(std::find(seen.begin(),seen.end(),to)!=seen.end())continue;
            seen.push_back(to);q.push({to,depth+1});
        }
    }
    for(const auto& tile:ct.get_tiles()) {
        const auto* p=tile.get_dragon();if(!p||!p->is_head()||p->get_id()==ct.get_id())continue;
        if(std::any_of(seen.begin(),seen.end(),[&](Position x){return x==tile.get_position()
             || x.add_dir(Direction::NORTH)==tile.get_position()||x.add_dir(Direction::SOUTH)==tile.get_position()
             || x.add_dir(Direction::EAST)==tile.get_position()||x.add_dir(Direction::WEST)==tile.get_position();}))++out.heads;
    }
    return out;
}
inline double reproduction_value(const Opportunity& o,int round) {
    // A late child has fewer turns to repay its opportunity cost. No hard
    // phase switch or fixed global population ceiling is used.
    const double time=std::min(1.0,std::max(0.0,(499-round)/24.0));
    return time*(70+12*std::min(4,o.food)+5*std::min(12,o.room)+8*std::min(3,o.frontier))
        -22*o.heads;
}
}
