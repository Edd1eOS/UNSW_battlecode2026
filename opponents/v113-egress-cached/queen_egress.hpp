#pragma once
#include "strategy.hpp"

namespace queen_egress {
using namespace strategy;

// A later worker must not close the visible Queen's last currently legal
// first step when an equally viable alternative exists. This evaluates the
// whole final worker body, not just its distance from the Queen.
struct Guard {
    const Controller& ct;
    const Memory& memory;
    Position queen{};
    bool active=false;
    int before=0;

    Guard(const Controller& c,const Memory& m):ct(c),memory(m) {
        if(c.get_id()<=1) return;
        for(const auto& tile:c.get_tiles()) {
            auto p=tile.get_dragon();
            if(p && p->is_head() && p->get_id()<=1 && p->get_team()==c.get_team()) {
                queen=tile.get_position();active=true;break;
            }
        }
        if(active) before=count(nullptr);
    }

    int count(const Simulation* after) const {
        if(!active) return 0;
        int exits=0;
        std::vector<Position> seen;
        for(auto d:Direction::get_direction_list()) {
            Position n;
            if(!memory.destination(ct,queen,d,n)) continue;
            const auto* tile=ct.get_tile(n);
            if(!tile) continue; // An unseen portal is not an assured exit.
            const auto* part=tile->get_dragon();
            if(part && (!after || part->get_id()!=ct.get_id() || !after->complete)) continue;
            if(after && std::find(after->body.begin(),after->body.end(),n)!=after->body.end()) continue;
            if(std::find(seen.begin(),seen.end(),n)!=seen.end()) continue;
            seen.push_back(n);++exits;
        }
        return exits;
    }

    int damage(const Simulation& after) const {
        if(!active) return 0;
        // A Queen already fully blocked is not falsely claimed as saved;
        // opening an exit is useful, leaving it blocked is the neutral case.
        int remaining=count(&after);
        if(before==0) return remaining>0 ? -1 : 0;
        return remaining==0 ? 1 : 0;
    }
};
}
