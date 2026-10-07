#pragma once
#include "strategy.hpp"

// One adversarial reply under frozen visible occupancy. A found route is a
// concrete conditional threat; absence of a route is never a survival proof.
namespace reply_search {
using namespace strategy;
enum class Status { NoWitness, Unknown, Witness };
struct Result { Status status=Status::NoWitness;int enemy=-1,steps=0,expanded=0; };
inline bool has(const std::vector<Position>& xs,Position p) {return std::find(xs.begin(),xs.end(),p)!=xs.end();}
inline std::deque<Position> complete_body(const Controller& ct,const Memory& m,int id) {
    std::deque<Position> body;
    for(const auto& t:ct.get_tiles())if(t.get_dragon()&&t.get_dragon()->get_id()==id&&t.get_dragon()->is_head())body.push_back(t.get_position());
    if(body.size()!=1)return {};
    for(int n=0;n<48;++n) {
        std::optional<Position> previous;
        const auto* tail=ct.get_tile(body.back());if(!tail)return {};
        for(const auto& t:ct.get_tiles())if(const auto* p=t.get_dragon()) {
            if(p->get_id()!=id||p->is_head())continue;
            Position next;if(!m.destination(ct,t.get_position(),p->get_dir(),next)||next!=body.back())continue;
            if(previous||std::find(body.begin(),body.end(),t.get_position())!=body.end())return {};
            previous=t.get_position();
        }
        if(!previous) {
            for(auto d:Direction::get_direction_list()) {
                const auto& e=tail->get_edge(d);if(e.is_portal())return {};
                if(e.get_edge_type()==EdgeType::KELP)continue;
                if(!ct.get_tile(body.back().add_dir(d)))return {};
            }
            int count=0;for(const auto& t:ct.get_tiles())if(t.get_dragon()&&t.get_dragon()->get_id()==id)++count;
            return count==int(body.size())?body:std::deque<Position>{};
        }
        body.push_back(*previous);
    }
    return {};
}
inline int distance(const Memory& m,Position a,Position b) {
    int x=std::abs(a.x-b.x),y=std::abs(a.y-b.y);return std::min(x,m.width-x)+std::min(y,m.height-y);
}
inline bool search(const Controller& ct,const Memory& m,const Simulation& queen,const std::vector<Position>& blocked,
                   int enemy,Simulation enemy_state,int free,int depth,int& budget,bool& unknown,int& found_steps) {
    if(depth>=10){unknown=true;return false;}
    if(budget--<=0){unknown=true;return false;}
    const bool paid=depth>=free;
    if(paid&&enemy_state.length<=2)return false;
    auto directions=Direction::get_direction_list();
    std::stable_sort(directions.begin(),directions.end(),[&](Direction a,Direction b){
        Position aa,bb;bool ka=m.destination(ct,enemy_state.body.front(),a,aa),kb=m.destination(ct,enemy_state.body.front(),b,bb);
        return (ka?distance(m,aa,queen.body.front()):999)<(kb?distance(m,bb,queen.body.front()):999);
    });
    for(auto d:directions) {
        Position to;if(!m.destination(ct,enemy_state.body.front(),d,to)){
            const auto* origin=ct.get_tile(enemy_state.body.front());
            if(!origin||origin->get_edge(d).is_portal())unknown=true;continue;
        }
        if(std::find(enemy_state.body.begin(),enemy_state.body.end(),to)!=enemy_state.body.end()||has(blocked,to))continue;
        const auto* tile=ct.get_tile(to);if(!tile){unknown=true;continue;}
        if(to==queen.body.front()){found_steps=depth+1;return true;}
        if(std::find(queen.body.begin(),queen.body.end(),to)!=queen.body.end())continue;
        if(const auto* p=tile->get_dragon())if(p->get_id()!=enemy&&p->get_id()!=ct.get_id())continue;
        Simulation next=enemy_state;const bool food=tile->has_pearl()&&!has(queen.eaten,to)&&!has(next.eaten,to);
        next.body.push_front(to);
        if(food){next.eaten.push_back(to);++next.length;}else next.body.pop_back();
        if(paid){--next.length;next.body.pop_back();}
        if(search(ct,m,queen,blocked,enemy,next,free,depth+1,budget,unknown,found_steps))return true;
    }
    return false;
}
inline Result assess(const Controller& ct,const Memory& m,const Simulation& queen,const std::vector<Position>& blocked={}) {
    Result r;if(!queen.complete||queen.body.empty())return {Status::Unknown};
    bool unknown=false;int budget=320;
    for(const auto& tile:ct.get_tiles())if(const auto* p=tile.get_dragon()) {
        if(!p->is_head()||p->get_team()==ct.get_team())continue;
        auto body=complete_body(ct,m,p->get_id());
        if(body.empty()){unknown=true;continue;}
        Simulation enemy{body,{},true,int(body.size())};int steps=0;
        if(search(ct,m,queen,blocked,p->get_id(),enemy,(enemy.length+3)/4,0,budget,unknown,steps))
            return {Status::Witness,p->get_id(),steps,320-std::max(0,budget)};
        if(budget<=0)break;
    }
    r.status=unknown?Status::Unknown:Status::NoWitness;r.expanded=320-std::max(0,budget);return r;
}
}
