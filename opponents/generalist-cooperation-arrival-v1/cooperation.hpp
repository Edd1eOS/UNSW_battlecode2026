#pragma once
#include "strategy.hpp"

// Conditional traffic evidence from this actor's legal observation only.
namespace cooperation {
using namespace strategy;
struct ExitEvidence {
    int before=0,after=0;
    bool unknown=false;
    bool seals() const {return before>0&&after==0&&!unknown;}
};
struct Queen {Position head;Direction facing;int id;};
struct Model {
    const Controller& ct;
    const Memory& memory;
    std::vector<Queen> queens;
    std::vector<bool> portal_arrival;
    Model(const Controller& controller,const Memory& m):ct(controller),memory(m),portal_arrival(m.cells.size(),false) {
        for(const auto& tile:ct.get_tiles()) {
            const auto* part=tile.get_dragon();
            if(part&&part->is_head()&&part->get_id()<=1&&part->get_id()!=ct.get_id()
               &&part->get_team()==ct.get_team())queens.push_back({tile.get_position(),part->get_dir(),part->get_id()});
            for(auto d:Direction::get_direction_list())if(tile.get_edge(d).is_portal()) {
                Position other;
                // Either side of a mouth can be a landing for a matching ray.
                // Unknown occupancy is possible traffic, never a collision.
                if(!m.destination(ct,tile.get_position(),d,other)||!ct.get_tile(other))
                    portal_arrival[m.index(tile.get_position())]=true;
            }
        }
    }
    bool in_queen_view(Position p,const Queen& queen) const {
        const auto within=[](int a,int b,int size){int n=(a-b+size)%size;return n<=3||n>=size-3;};
        return within(p.x,queen.head.x,memory.width)&&within(p.y,queen.head.y,memory.height);
    }
    template<class Body>
    ExitEvidence exits(const Queen& queen,const Body& post_body,const std::vector<Position>& extra={}) const {
        ExitEvidence out;
        for(auto d:Direction::get_direction_list()) {
            // Every live dragon has at least two segments. Its facing proves
            // the old neck even when a portal hides that segment.
            if(d==queen.facing.get_opposite())continue;
            Position to;
            const auto* head=ct.get_tile(queen.head);
            if(!memory.destination(ct,queen.head,d,to)) {
                if(head&&head->get_edge(d).is_portal())out.unknown=true;
                continue;
            }
            const auto* tile=ct.get_tile(to);
            if(!tile||!in_queen_view(to,queen)){out.unknown=true;continue;}
            const auto* part=tile->get_dragon();
            if(!part)++out.before;
            bool occupied=std::find(post_body.begin(),post_body.end(),to)!=post_body.end()
                ||std::find(extra.begin(),extra.end(),to)!=extra.end();
            // Other units are retained as a conditional current snapshot;
            // this does not promise that their bodies stay fixed next round.
            if(part&&part->get_id()!=ct.get_id())occupied=true;
            if(!occupied)++out.after;
        }
        return out;
    }
    template<class Body>
    bool seals_any(const Body& post_body,const std::vector<Position>& extra={}) const {
        for(const auto& queen:queens)if(exits(queen,post_body,extra).seals())return true;
        return false;
    }
    template<class Body>
    bool preserves_all(const Body& post_body,const std::vector<Position>& extra={}) const {
        if(queens.empty())return false;
        for(const auto& queen:queens){const auto e=exits(queen,post_body,extra);
            if(e.before<=0||e.after<=0||e.unknown)return false;}
        return true;
    }
    double arrival_cost(Position endpoint) const {
        return portal_arrival[memory.index(endpoint)]?120.0:0.0;
    }
};
} // namespace cooperation
