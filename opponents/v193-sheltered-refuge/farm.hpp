#pragma once
#include "forage.hpp"
namespace farm {
using namespace strategy;
struct State {int tag=-1;std::vector<Position> cycle;};
inline Direction direction(Position a,Position b){
    for(auto d:Direction::get_direction_list())if(a.add_dir(d)==b)return d;
    return Direction(Direction::NORTH);
}
inline bool choose(const Controller& ct,const Memory& m,State& state,forage::Plan& plan){
    if(ct.get_id()>1 || plan.action.child_size || (int)m.body.size()!=ct.get_length())return false;
    for(const auto& t:ct.get_tiles())if(auto p=t.get_dragon())
        if(p->get_team()!=ct.get_team())return false;
    auto head=ct.get_position();
    auto clear=[&](const std::vector<Position>& cycle){
        for(int i=0;i<(int)cycle.size();++i){
            auto p=cycle[i],n=cycle[(i+1)%cycle.size()];const auto* tile=ct.get_tile(p);
            if(!tile || tile->get_edge(direction(p,n)).get_edge_type()!=unswbc::EdgeType::EMPTY)return false;
            auto part=tile->get_dragon();if(part&&part->get_id()!=ct.get_id())return false;
        }return true;
    };
    if(!state.cycle.empty() && std::find(state.cycle.begin(),state.cycle.end(),head)!=state.cycle.end()
       && clear(state.cycle) && ct.get_length()>=(int)state.cycle.size()-1 && ct.can_split(2)){
        plan={{ct.get_dir(),2},{},"OCT8 FARM_SPACE"};return true;
    }
    double best=0;std::vector<Position> bestcycle;int tag=-1;
    auto wrap=[&](int x,int y){return Position{(x+m.width)%m.width,(y+m.height)%m.height};};
    for(int w=2;w<=4;++w)for(int h=2;h<=4;++h)for(int dx=1-w;dx<=0;++dx)for(int dy=1-h;dy<=0;++dy){
        int x=head.x+dx,y=head.y+dy;
        std::vector<Position> ring;
        for(int a=0;a<w;++a)ring.push_back(wrap(x+a,y));
        for(int b=1;b<h;++b)ring.push_back(wrap(x+w-1,y+b));
        for(int a=w-2;a>=0;--a)ring.push_back(wrap(x+a,y+h-1));
        for(int b=h-2;b>0;--b)ring.push_back(wrap(x,y+b));
        if(std::find(ring.begin(),ring.end(),head)==ring.end() || (int)ring.size()<ct.get_length()+1 || !clear(ring))continue;
        double yield=0;int spawns=0;
        for(auto p:ring){auto t=ct.get_tile(p);yield+=t->has_pearl()?1:0;
            if(t->get_pearl_time()>=0){++spawns;yield+=0.2+2.0/(4+t->get_pearl_time());}}
        int walls=0;for(auto p:ring)for(auto d:Direction::get_direction_list())if(ct.get_tile(p)->get_edge(d).get_edge_type()==unswbc::EdgeType::KELP)++walls;
        if(walls<(int)ring.size())continue;
        for(int reverse=0;reverse<2;++reverse){
            if(reverse)std::reverse(ring.begin(),ring.end());
            auto found=std::find(ring.begin(),ring.end(),head);std::rotate(ring.begin(),found,ring.end());
            Simulation sim{m.body,{},true,ct.get_length()};bool safe=true;
            for(int i=1;i<=2*(int)ring.size();++i){
                auto n=ring[i%ring.size()];if(!simulate_step(ct,sim,direction(sim.body.front(),n),&m)){safe=false;break;}
            }
            if(!safe)continue;
            int identity=((m.index(wrap(x,y))*5+w)*5+h)*2+reverse;
            double score=(10.0+walls*2.0-yield)/ring.size()*(identity==state.tag?2.0:1.0);
            if(score>best){best=score;bestcycle=ring;tag=identity;}
        }
    }
    if(bestcycle.empty()){state.tag=-1;state.cycle.clear();return false;}
    state.tag=tag;state.cycle=bestcycle;auto d=direction(head,bestcycle[1]);
    plan={{d,0},{d},"OCT8 FARM_CYCLE n="+std::to_string(bestcycle.size())};return true;
}
}
