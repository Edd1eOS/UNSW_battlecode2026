#pragma once
#include "strategy.hpp"

// A current-view arrival auction. These are navigation claims, not food
// income, another dragon's full length, or a commitment to its next action.
namespace allocation {
using namespace strategy;
struct Agent { int id=0,length_lower_bound=2;Position head;bool own=false,queen=false; };
struct Result {
    std::vector<Agent> agents;
    std::vector<Position> resources;
    std::vector<int> owner;
    int target=-1,self_eta=-1,work=0;
    bool contested=false,exhausted=false,unknown=false,depth_truncated=false,agents_truncated=false,resources_truncated=false;
    bool claimed_by_other(int cell,const Memory& m,int own_id)const {
        for(int k=0;k<static_cast<int>(resources.size());++k)
            if(m.index(resources[k])==cell&&owner[k]>=0&&owner[k]!=own_id)return true;
        return false;
    }
};
inline std::vector<int> distances(const Controller& ct,const Memory& m,const Agent& agent,Result& out,
                                  const std::vector<Position>& targets) {
    std::vector<int> dist(m.cells.size(),9999);std::queue<Position> q;
    std::vector<bool> needed(m.cells.size(),false);int remaining=0;
    for(auto p:targets)if(p!=agent.head&&!needed[m.index(p)]){needed[m.index(p)]=true;++remaining;}
    q.push(agent.head);dist[m.index(agent.head)]=0;int budget=2048;
    while(!q.empty()&&budget>0&&remaining>0) {
        auto at=q.front();q.pop();--budget;++out.work;const int depth=dist[m.index(at)];
        if(depth>=32){out.depth_truncated=true;continue;}
        for(auto d:Direction::get_direction_list()) {
            Position to;if(!m.destination(ct,at,d,to)) {
                const auto* from=m.cell(at);if(from&&from->edges[Atlas::direction_index(d)].is_portal())out.unknown=true;
                continue;
            }
            const auto* cell=m.cell(to);if(!cell||!cell->known){out.unknown=true;continue;}
            const auto* tile=ct.get_tile(to);const auto* part=tile?tile->get_dragon():nullptr;
            // Own occupancy is optimistic navigation only; actual movement
            // still checks the complete old body in the existing planner.
            if(part&&part->get_id()!=agent.id)continue;
            const int i=m.index(to);if(dist[i]!=9999)continue;
            dist[i]=depth+1;q.push(to);
            if(needed[i]){needed[i]=false;--remaining;}
        }
    }
    // Stopping after every requested resource has its exact BFS distance is
    // completion for this auction, not work exhaustion or a full-map claim.
    if(remaining>0&&!q.empty())out.exhausted=true;
    return dist;
}
template<class VisibleLength>
inline Result build(const Controller& ct,const Memory& m,VisibleLength visible_length) {
    Result out;
    out.agents.push_back({ct.get_id(),ct.get_length(),ct.get_position(),true,ct.get_id()<=1});
    for(const auto& tile:ct.get_tiles()) {
        const auto* p=tile.get_dragon();
        if(p&&p->is_head()&&p->get_team()==ct.get_team()&&p->get_id()!=ct.get_id())
            out.agents.push_back({p->get_id(),std::max(2,visible_length(p->get_id())),tile.get_position(),false,p->get_id()<=1});
        if(tile.has_pearl()&&!p)out.resources.push_back(tile.get_position());
    }
    if(out.agents.size()==1||out.resources.empty()){out.owner.assign(out.resources.size(),-1);return out;}
    std::stable_sort(out.agents.begin()+1,out.agents.end(),[](const Agent& a,const Agent& b){return a.id<b.id;});
    if(out.agents.size()>8){out.agents.resize(8);out.agents_truncated=true;}
    std::vector<std::vector<int>> dist;
    dist.push_back(distances(ct,m,out.agents.front(),out,out.resources));
    std::stable_sort(out.resources.begin(),out.resources.end(),[&](Position a,Position b){
        const int da=dist[0][m.index(a)],db=dist[0][m.index(b)];
        return da!=db?da<db:m.index(a)<m.index(b);});
    if(out.resources.size()>12){out.resources.resize(12);out.resources_truncated=true;}
    out.owner.assign(out.resources.size(),-1);
    // No verified self bid means this auction can never become contested;
    // preserve the old navigation rather than scanning seven irrelevant peers.
    if(std::none_of(out.resources.begin(),out.resources.end(),[&](Position p){return dist[0][m.index(p)]<9999;}))return out;
    for(int a=1;a<static_cast<int>(out.agents.size());++a)
        dist.push_back(distances(ct,m,out.agents[a],out,out.resources));
    struct Bid {int agent,resource,eta,distance;bool queen_priority;};
    std::vector<Bid> bids;
    for(int resource=0;resource<static_cast<int>(out.resources.size());++resource) {
        const int i=m.index(out.resources[resource]);int best=9999;
        std::vector<int> eta(out.agents.size(),9999);
        for(int a=0;a<static_cast<int>(out.agents.size());++a)if(dist[a][i]<9999) {
            const int free=std::max(1,(out.agents[a].length_lower_bound+3)/4);
            eta[a]=(dist[a][i]+free-1)/free;best=std::min(best,eta[a]);
        }
        // Only verified competing routes activate the replacement. An
        // unfound route after the work/depth cap is not proof of absence.
        if(eta[0]<9999)for(int a=1;a<static_cast<int>(eta.size());++a)
            if(eta[a]<9999)out.contested=true;
        for(int a=0;a<static_cast<int>(out.agents.size());++a)if(eta[a]<9999)
            bids.push_back({a,resource,eta[a],dist[a][i],out.agents[a].queen&&eta[a]<=best+1});
    }
    if(!out.contested)return out;
    std::stable_sort(bids.begin(),bids.end(),[&](const Bid& a,const Bid& b){
        if(a.queen_priority!=b.queen_priority)return a.queen_priority>b.queen_priority;
        if(a.eta!=b.eta)return a.eta<b.eta;
        if(a.distance!=b.distance)return a.distance<b.distance;
        if(out.agents[a.agent].id!=out.agents[b.agent].id)return out.agents[a.agent].id<out.agents[b.agent].id;
        return m.index(out.resources[a.resource])<m.index(out.resources[b.resource]);});
    std::vector<bool> assigned(out.agents.size(),false);
    for(const auto& bid:bids)if(!assigned[bid.agent]&&out.owner[bid.resource]<0) {
        assigned[bid.agent]=true;out.owner[bid.resource]=out.agents[bid.agent].id;
        if(bid.agent==0){out.target=m.index(out.resources[bid.resource]);out.self_eta=bid.eta;}
    }
    return out;
}
} // namespace allocation
