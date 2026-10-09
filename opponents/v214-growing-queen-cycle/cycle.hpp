#pragma once
#include "forage.hpp"
namespace cycle {
using namespace strategy;
struct State {std::vector<Position> ring;};
inline bool edge(const Controller& ct,const Memory& m,Position a,Position b,Direction& out){
    for(auto d:Direction::get_direction_list()){Position n;if(m.destination(ct,a,d,n)&&n==b){out=d;return true;}}return false;
}
inline bool choose(const Controller& ct,const Memory& m,State& st,forage::Plan& plan){
    if(ct.get_id()>1 || plan.action.child_size || (int)m.body.size()!=ct.get_length())return false;
    for(const auto& t:ct.get_tiles())if(auto p=t.get_dragon())if(p->get_team()!=ct.get_team()){st.ring.clear();return false;}
    auto head=ct.get_position();Direction d=ct.get_dir();
    auto usable=[&](const std::vector<Position>& r){
        if(r.size()<4)return false;
        for(int i=0;i<(int)r.size();++i){auto t=ct.get_tile(r[i]);if(t&&t->get_dragon()&&t->get_dragon()->get_id()!=ct.get_id())return false;
            Direction step=ct.get_dir();if(!edge(ct,m,r[i],r[(i+1)%r.size()],step))return false;}
        return true;
    };
    auto it=std::find(st.ring.begin(),st.ring.end(),head);
    if(it!=st.ring.end()&&usable(st.ring)){
        std::rotate(st.ring.begin(),it,st.ring.end());
        if(ct.get_length()>=(int)st.ring.size()-1 && ct.can_split(2)){plan={{ct.get_dir(),2},{},"CYCLE GROWTH_RELEASE"};return true;}
        Simulation sim{m.body,{},true,ct.get_length()};
        if(ct.get_length()<(int)st.ring.size()-1 && edge(ct,m,head,st.ring[1],d)&&simulate_step(ct,sim,d,&m)){
            plan={{d,0},{d},"CYCLE FOLLOW n="+std::to_string(st.ring.size())};return true;}
    }
    st.ring.clear();std::vector<Position> path{head},best;std::vector<bool> seen(m.cells.size(),false);seen[m.index(head)]=true;
    int budget=900;double bestscore=-1;
    auto visit=[&](auto&& self,Position at)->void{
        if(--budget<0 || path.size()>20)return;
        for(auto dir:Direction::get_direction_list()){
            Position n;if(!m.destination(ct,at,dir,n))continue;auto t=ct.get_tile(n);if(!t)continue;
            if(n==head){
                if(path.size()<4 || (int)path.size()<ct.get_length()+2)continue;
                Simulation sim{m.body,{},true,ct.get_length()};bool safe=true;int walls=0;double food=0;
                for(int i=1;i<=2*(int)path.size();++i){Direction move=ct.get_dir();if(!edge(ct,m,sim.body.front(),path[i%path.size()],move)||!simulate_step(ct,sim,move,&m)){safe=false;break;}}
                if(!safe)continue;
                for(auto p:path){auto tile=ct.get_tile(p);food+=tile->has_pearl()?1:0;food+=tile->get_pearl_time()>=0?0.3:0;
                    for(auto a:Direction::get_direction_list())walls+=tile->get_edge(a).get_edge_type()==EdgeType::KELP;}
                double score=path.size()+2.0*food+0.2*walls;
                if(score>bestscore){bestscore=score;best=path;}continue;
            }
            if(seen[m.index(n)])continue;auto p=t->get_dragon();if(p&&p->get_id()!=ct.get_id())continue;
            seen[m.index(n)]=true;path.push_back(n);self(self,n);path.pop_back();seen[m.index(n)]=false;
            if(budget<0)return;
        }
    };visit(visit,head);
    if(best.empty())return false;st.ring=best;edge(ct,m,head,best[1],d);plan={{d,0},{d},"CYCLE FOUND n="+std::to_string(best.size())};return true;
}
}
