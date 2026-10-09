#pragma once
#include "forage.hpp"
namespace swarm {
using namespace strategy;
inline forage::Plan choose(const Controller& ct, Memory& m, forage::State& state){
    if(ct.get_id()<=1 || m.now>=400 || ct.get_length()>8)return forage::choose(ct,m,state);
    auto attack=forage::attack_queen(ct,m);
    if(!attack.empty())return {{attack[0],0},attack,"OCT8 SWARM_QUEEN"};
    attack=forage::attack_queen(ct,m,true);
    if(!attack.empty())return {{attack[0],0},attack,"OCT8 SWARM_TRADE"};
    auto danger=forage::danger_map(ct,m);
    if(ct.can_split(2) && ct.get_unit_count()<60 && (int)m.body.size()==ct.get_length()
       && nearby_threats(ct,ct.get_position())==0){
        auto tail=m.body.back();int exits=0;
        for(auto d:Direction::get_direction_list()){
            Position n;if(!m.destination(ct,tail,d,n))continue;auto t=ct.get_tile(n);
            if(t&&!t->get_dragon()&&danger[m.index(n)]<1)++exits;
        }
        if(exits && forage::queen_crowding(ct,tail)<=1)return {{ct.get_dir(),ct.get_length()/2},{},"OCT8 SWARM_BROOD"};
    }
    double best=-1e30;Direction move=ct.get_dir();bool found=false;
    for(auto d:Direction::get_direction_list()){
        Simulation sim{m.body,{},(int)m.body.size()==ct.get_length(),ct.get_length()};
        if(!simulate_step(ct,sim,d,&m))continue;
        auto n=sim.body.front();auto e=evaluate(ct,n,&m);int budget=50;
        auto future=search_survival(ct,sim,0,3,budget,&m);
        double score=sim.eaten.size()*180.0 + 160.0/(1+e.pearl_distance)
            +25.0/(1+e.frontier_distance)+std::min(20,e.space)*0.4
            -danger[m.index(n)]*85.0-6*m.visits(n)-0.8*std::min(20,m.lifetime_visits(n));
        if(!future.uncertain && future.depth<3)score-=200;
        if(d==ct.get_dir())score+=0.1;
        if(score>best){best=score;move=d;found=true;}
    }
    if(!found)return forage::choose(ct,m,state);
    return {{move,0},{move},"OCT8 LOCAL_SWARM"};
}
}
