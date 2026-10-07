#pragma once
#include "strategy.hpp"

namespace emergency {
using namespace strategy;
struct Evidence { int depth=0;bool unknown=false,portal=false,budget=false; };
struct Assessment {
    Simulation parent,child;
    Evidence parent_future,child_future;
    bool complete=false,facing_known=false,child_no_first_move=false,parent_no_first_move=false,reject=false;
};
inline bool has(const std::deque<Position>& body,Position p){return std::find(body.begin(),body.end(),p)!=body.end();}
inline Evidence search(const Controller& ct,const Memory& m,const Simulation& current,
                       const std::deque<Position>& sibling,bool stationary_sibling,Direction facing,
                       int depth,int& budget) {
    Evidence best;best.depth=depth;
    if(depth>=2)return best;
    if(budget--<=0){best.budget=true;return best;}
    // The inherited step simulator needs a current source Tile, even when
    // Atlas remembers its terrain. Missing input is unresolved, not closure.
    if(!ct.get_tile(current.body.front())){best.unknown=true;return best;}
    const auto* from=m.cell(current.body.front());
    if(!from||!from->known){best.unknown=true;return best;}
    for(auto d:Direction::get_direction_list()) {
        // Old-neck collision is before food/tail removal, including portals.
        if(current.length>=2&&d==facing.get_opposite())continue;
        Position to;
        if(!m.destination(ct,current.body.front(),d,to)) {
            if(from->edges[Atlas::direction_index(d)].is_portal())best.portal=true;
            continue;
        }
        if(has(current.body,to))continue;
        if(has(sibling,to)) {if(!stationary_sibling)best.unknown=true;continue;}
        const auto* tile=ct.get_tile(to);
        if(!tile){best.unknown=true;continue;}
        const auto* part=tile->get_dragon();
        // Other actors can move before this newborn's new-ID turn. Frozen
        // foreign occupancy cannot certify a permanently closed birth exit.
        if(part&&part->get_id()!=ct.get_id()){best.unknown=true;continue;}
        Simulation next=current;
        if(!simulate_step(ct,next,d,&m))continue;
        // One free step per modeled future action is sufficient. This is not
        // an assertion that a long child's actual birth quota equals one.
        auto future=search(ct,m,next,sibling,stationary_sibling,d,depth+1,budget);
        best.depth=std::max(best.depth,future.depth);
        best.unknown|=future.unknown;best.portal|=future.portal;best.budget|=future.budget;
    }
    return best;
}
inline bool closed_first(const Evidence& e){return e.depth==0&&!e.unknown&&!e.portal&&!e.budget;}
inline Assessment assess(const Controller& ct,const Memory& m,const Simulation& original,int child_size) {
    Assessment a;
    if(!original.complete||static_cast<int>(original.body.size())!=ct.get_length()||!ct.can_split(child_size))return a;
    a.complete=true;a.parent=original;a.parent.length-=child_size;a.parent.body.resize(a.parent.length);
    a.child.length=child_size;a.child.complete=true;
    for(int k=0;k<child_size;++k)a.child.body.push_back(original.body[original.body.size()-1-k]);
    Direction facing=ct.get_dir();
    for(auto d:Direction::get_direction_list()){Position to;
        if(m.destination(ct,a.child.body[1],d,to)&&to==a.child.body.front()){facing=d;a.facing_known=true;break;}}
    int parent_budget=32,child_budget=32;
    // Child may move or disappear before the parent's next turn.
    a.parent_future=search(ct,m,a.parent,a.child.body,false,ct.get_dir(),0,parent_budget);
    if(a.facing_known)a.child_future=search(ct,m,a.child,a.parent.body,true,facing,0,child_budget);
    else a.child_future.unknown=true;
    a.parent_no_first_move=closed_first(a.parent_future);
    a.child_no_first_move=a.facing_known&&closed_first(a.child_future);
    // A longer actor can split again even without a MOVE. Only two L2 actors
    // with no unresolved first exit have no ordinary move or split action.
    a.reject=a.parent.length==2&&a.child.length==2&&a.parent_no_first_move&&a.child_no_first_move;
    return a;
}
} // namespace emergency
