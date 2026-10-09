#pragma once
#include "strategy.hpp"
#include <array>
#include <cmath>

// A local counterfactual, never an executed-income ledger. Foreign bodies
// remain frozen at the current observation; unknown steps are not executed.
namespace investment {
using namespace unswbc;
using strategy::Memory;
using strategy::Simulation;
enum class Step { Legal, Blocked, Unaffordable, Outside, Portal };
struct Actor {
    std::deque<Position> body;
    int length=0;
    Direction facing=Direction::EAST;
};
struct Record {
    int actor=0,start_length=0,free_steps=0,food=0,paid=0;
    std::vector<Direction> moves;
};
struct World {
    std::array<Actor,2> actors;
    int count=1,food=0,paid=0;
    bool full_body=true;
    double risk_cost=0;
    std::vector<Position> eaten;
    std::vector<Record> records;
};
inline bool has(const std::vector<Position>& p,Position q) {
    return std::find(p.begin(),p.end(),q)!=p.end();
}
inline Step step(const Controller& ct,const Memory& m,World& w,int actor,Direction d,bool paid) {
    auto& a=w.actors[actor];
    if(paid&&a.length<=2)return Step::Unaffordable;
    Position to;
    if(!m.destination(ct,a.body.front(),d,to)) {
        const auto* here=ct.get_tile(a.body.front());
        return here&&here->get_edge(d).is_portal()?Step::Portal:Step::Blocked;
    }
    // Check every OLD body, including old tails, before food or payment.
    for(int j=0;j<w.count;++j)
        if(std::find(w.actors[j].body.begin(),w.actors[j].body.end(),to)!=w.actors[j].body.end())return Step::Blocked;
    const auto* tile=ct.get_tile(to);
    if(!tile)return Step::Outside;
    if(const auto* p=tile->get_dragon())
        if(p->get_id()!=ct.get_id()||!w.full_body)return Step::Blocked;
    const bool food=tile->has_pearl()&&!has(w.eaten,to);
    a.body.push_front(to);
    if(food){++a.length;++w.food;w.eaten.push_back(to);}else a.body.pop_back();
    if(paid){--a.length;++w.paid;a.body.pop_back();}
    a.facing=d;
    return Step::Legal;
}
inline bool apply_action(const Controller& ct,const Memory& m,World& w,int actor,const std::vector<Direction>& moves) {
    if(moves.empty())return false;
    World next=w;auto& a=next.actors[actor];
    Record r;r.actor=actor;r.start_length=a.length;r.free_steps=(a.length+3)/4;r.moves=moves;
    if(a.length>=2&&moves.front()==a.facing.get_opposite())return false;
    const int oldFood=next.food,oldPaid=next.paid;
    for(int k=0;k<static_cast<int>(moves.size());++k)
        if(step(ct,m,next,actor,moves[k],k>=r.free_steps)!=Step::Legal)return false;
    r.food=next.food-oldFood;r.paid=next.paid-oldPaid;next.records.push_back(r);w=std::move(next);
    return true;
}
inline bool split_world(const Controller& ct,const Memory& m,const Simulation& original,int child,World& out) {
    if(!original.complete||original.length!=ct.get_length()
       ||static_cast<int>(original.body.size())!=original.length||!ct.can_split(child))return false;
    for(std::size_t k=0;k<original.body.size();++k)
        if(std::find(original.body.begin()+k+1,original.body.end(),original.body[k])!=original.body.end())return false;
    World w;w.count=2;w.actors[0]={original.body,original.length-child,ct.get_dir()};
    w.actors[0].body.resize(w.actors[0].length);
    w.actors[1].length=child;
    for(int k=0;k<child;++k)w.actors[1].body.push_back(original.body[original.body.size()-1-k]);
    bool facing=false;
    for(auto d:Direction::get_direction_list()) {
        Position to;
        if(m.destination(ct,w.actors[1].body[1],d,to)&&to==w.actors[1].body.front()) {
            w.actors[1].facing=d;facing=true;break;
        }
    }
    if(!facing)return false;
    w.eaten=original.eaten;w.food=static_cast<int>(original.eaten.size());out=std::move(w);return true;
}
struct Context {
    const Controller& ct;
    const Memory& memory;
    const std::vector<double>* danger=nullptr;
    const std::vector<bool>* birth=nullptr;
    double resource_weight=110,parent_risk_weight=160,child_risk_weight=114;
    std::vector<int> local_index;
    std::vector<std::vector<int>> frontier_distance;
    explicit Context(const Controller& c,const Memory& m):ct(c),memory(m) {
        local_index.assign(m.cells.size(),-1);
        const auto& tiles=ct.get_tiles();
        for(int k=0;k<static_cast<int>(tiles.size());++k)local_index[m.index(tiles[k].get_position())]=k;
        std::vector<std::vector<int>> reverse(tiles.size());std::vector<int> sources;
        for(int k=0;k<static_cast<int>(tiles.size());++k) {
            const auto& tile=tiles[k];bool frontier=false;
            for(auto d:Direction::get_direction_list()) {
                Position to;
                if(!m.destination(ct,tile.get_position(),d,to)) {if(tile.get_edge(d).is_portal())frontier=true;continue;}
                const auto* cell=m.cell(to);if(!cell)continue;
                if(!cell->known)frontier=true;
                const auto* next=ct.get_tile(to);
                if(!next)continue;
                const auto* part=next->get_dragon();
                if(part&&part->get_id()!=ct.get_id())continue;
                reverse[local_index[m.index(to)]].push_back(k);
            }
            if(frontier)sources.push_back(k);
        }
        // Different frontier cells are opportunities, not imagined pearls.
        for(int source:sources) {
            std::vector<int> dist(tiles.size(),-1);std::queue<int> q;q.push(source);dist[source]=0;
            while(!q.empty()) {int at=q.front();q.pop();for(int before:reverse[at])
                if(dist[before]<0){dist[before]=dist[at]+1;q.push(before);}}
            frontier_distance.push_back(std::move(dist));
        }
    }
    double exploration(const World& w)const {
        double total=0;
        for(const auto& dist:frontier_distance) {
            double best=0;
            for(int j=0;j<w.count;++j) {
                const int k=local_index[memory.index(w.actors[j].body.front())];
                if(k>=0&&dist[k]>=0)best=std::max(best,1.0/(1+dist[k]));
            }
            total+=best; // Two actors at the same opportunity cannot double it.
        }
        return total;
    }
    double risk(const World& w,int actor)const {
        const int k=memory.index(w.actors[actor].body.front());
        return ((danger?(*danger)[k]:0)+(birth&&(*birth)[k]?0.35:0))
            *(actor==0?parent_risk_weight:child_risk_weight);
    }
    double value(const World& w)const {
        return resource_weight*(w.food-w.paid)-15*w.paid-w.risk_cost+3*exploration(w);
    }
};
struct Forecast {
    bool valid=false,complete=false,unknown=false,exhausted=false,closed=false;
    int food=0,paid=0,nodes=0;
    double exploration=0,value=-1e30;
    World world;
};
struct ActionNode { World world;std::vector<Direction> moves;int start_length=0,free_steps=0; };
inline std::vector<World> actions(const Controller& ct,const Memory& m,const World& origin,int actor,
                                  const Context& context,int& budget,Forecast& flags) {
    const int start=origin.actors[actor].length,free=(start+3)/4,limit=std::min(6,free+2),width=4;
    std::vector<ActionNode> beam{{origin,{},start,free}};
    std::vector<World> endpoints;
    for(int depth=0;depth<limit&&!beam.empty();++depth) {
        std::vector<ActionNode> next;
        for(const auto& parent:beam)for(auto d:Direction::get_direction_list()) {
            if(budget<=0){flags.exhausted=true;break;}--budget;++flags.nodes;
            if(depth==0&&start>=2&&d==origin.actors[actor].facing.get_opposite())continue;
            ActionNode c=parent;const auto result=step(ct,m,c.world,actor,d,depth>=free);
            if(result==Step::Outside||result==Step::Portal){flags.unknown=true;continue;}
            if(result!=Step::Legal)continue;
            c.moves.push_back(d);World end=c.world;
            Record r;r.actor=actor;r.start_length=start;r.free_steps=free;r.moves=c.moves;
            r.food=end.food-origin.food;r.paid=end.paid-origin.paid;
            end.records.push_back(r);end.risk_cost+=context.risk(end,actor);
            endpoints.push_back(std::move(end));next.push_back(std::move(c));
        }
        std::stable_sort(next.begin(),next.end(),[&](const ActionNode& a,const ActionNode& b){
            return context.value(a.world)-context.risk(a.world,actor)>context.value(b.world)-context.risk(b.world,actor);});
        if(static_cast<int>(next.size())>width)next.resize(width);beam=std::move(next);
        if(budget<=0)break;
    }
    std::stable_sort(endpoints.begin(),endpoints.end(),[&](const World& a,const World& b){return context.value(a)>context.value(b);});
    if(static_cast<int>(endpoints.size())>width)endpoints.resize(width);
    return endpoints;
}
inline Forecast schedule(const Controller& ct,const Memory& m,World initial,const std::vector<int>& turns,
                          const Context& context,int budget) {
    Forecast f;f.world=initial;f.valid=true;f.food=initial.food;f.paid=initial.paid;
    std::vector<World> beam{std::move(initial)};
    for(int actor:turns) {
        std::vector<World> next;
        for(const auto& w:beam) {
            auto end=actions(ct,m,w,actor,context,budget,f);
            next.insert(next.end(),std::make_move_iterator(end.begin()),std::make_move_iterator(end.end()));
            if(budget<=0)break;
        }
        if(next.empty()){f.closed=!f.unknown&&!f.exhausted;return f;}
        std::stable_sort(next.begin(),next.end(),[&](const World& a,const World& b){return context.value(a)>context.value(b);});
        if(next.size()>4)next.resize(4);beam=std::move(next);
    }
    f.complete=true;f.world=std::move(beam.front());f.food=f.world.food;f.paid=f.world.paid;
    f.exploration=context.exploration(f.world);f.value=context.value(f.world);return f;
}
inline Forecast evaluate_split(const Controller& ct,const Memory& m,const Simulation& original,int child,
                                const Context& context,int budget=320) {
    World w;if(!split_world(ct,m,original,child,w))return {};
    // t: parent SPLIT (stationary), newborn MOVE. t+1: parent then child.
    return schedule(ct,m,std::move(w),{1,0,1},context,budget);
}
inline Forecast evaluate_move(const Controller& ct,const Memory& m,const Simulation& after,
                               const std::vector<Direction>& current,int paid,const Context& context,int budget=96) {
    if(!after.complete||current.empty())return {};
    World w;w.actors[0]={after.body,after.length,current.back()};w.eaten=after.eaten;
    w.food=static_cast<int>(after.eaten.size());w.paid=paid;
    // t: the candidate MOVE already applied. t+1: the same actor's MOVE.
    return schedule(ct,m,std::move(w),{0},context,budget);
}
} // namespace investment
