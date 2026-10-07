#pragma once
#include "strategy.hpp"

// Possible split-tail attacks from legal current vision. These are hypotheses,
// never confirmed tails, exact rival lengths, or a hard physical safety oracle.
namespace born_threat {
using namespace strategy;
struct BirthThreat {
    std::vector<bool> same_round_possible, next_round_possible;
    bool unresolved_portal=false;
};
inline BirthThreat build(const Controller& ct,const Memory& m) {
    BirthThreat result;
    result.same_round_possible.assign(m.cells.size(),false);
    result.next_round_possible.assign(m.cells.size(),false);
    const auto& tiles=ct.get_tiles();
    for(const auto& tail:tiles) {
        const auto* part=tail.get_dragon();
        if(!part || part->is_head() || part->get_team()==ct.get_team())continue;
        const int parent=part->get_id();const Position origin=tail.get_position();
        Position neck;
        if(!m.destination(ct,origin,part->get_dir(),neck))continue;
        const auto* neckTile=ct.get_tile(neck);
        const auto* neckPart=neckTile?neckTile->get_dragon():nullptr;
        if(!neckPart || neckPart->get_id()!=parent || neckPart->is_head())continue;
        // A visible successor proves this segment is not the old tail.
        bool successor=false;
        for(const auto& other:tiles) {
            const auto* op=other.get_dragon();Position to;
            if(!op || op->is_head() || op->get_id()!=parent || other.get_position()==origin)continue;
            if(m.destination(ct,other.get_position(),op->get_dir(),to)&&to==origin) {
                successor=true;break;
            }
        }
        if(successor)continue;
        // If this were the tail, a fully visible tail-to-head chain of fewer
        // than four segments cannot split two while leaving a legal parent.
        Position cursor=neck;int count=2;bool shortParent=false;
        while(count<4) {
            const auto* tile=ct.get_tile(cursor);const auto* cp=tile?tile->get_dragon():nullptr;
            if(!cp || cp->get_id()!=parent)break;
            if(cp->is_head()){shortParent=true;break;}
            Position to;if(!m.destination(ct,cursor,cp->get_dir(),to))break;
            cursor=to;++count;
        }
        if(shortParent)continue;
        // Split reverses the old last two segments. The new L2 child receives
        // one free step later in this same round, including if created late.
        // The old parent does not move when it splits, so its known segments
        // and the child's old neck remain solid. Other units may have moved;
        // ignoring their occupancy is deliberately a possible-attack bound.
        for(auto d:Direction::get_direction_list()) {
            Position to;
            if(!m.destination(ct,origin,d,to)) {
                if(tail.get_edge(d).is_portal())result.unresolved_portal=true;
                continue;
            }
            if(to==origin || to==neck || !m.cell(to))continue;
            const auto* landing=ct.get_tile(to);const auto* lp=landing?landing->get_dragon():nullptr;
            if(lp && lp->get_id()==parent)continue;
            auto& flags=parent>ct.get_id()?result.same_round_possible:result.next_round_possible;
            flags[m.index(to)]=true;
        }
    }
    return result;
}
}
