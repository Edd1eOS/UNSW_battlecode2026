#pragma once
#include "strategy.hpp"
namespace postmove_space {
using namespace strategy;
inline Evaluation evaluate_after(const Controller& ct,const Memory& m,const Simulation& s){
    Evaluation out;const auto& tiles=ct.get_tiles();auto first=ct.get_tile(s.body.front());if(!first)return out;
    std::vector<int> dist(tiles.size(),-1);std::vector<bool> blocked(tiles.size(),false);
    for(int i=0;i<(int)tiles.size();++i){auto p=tiles[i].get_dragon();blocked[i]=p&&(p->get_id()!=ct.get_id()||!s.complete);}
    for(auto p:s.body){auto t=ct.get_tile(p);if(t)blocked[t-tiles.data()]=true;}
    int start=first-tiles.data();blocked[start]=false;dist[start]=0;std::queue<int> q;q.push(start);
    while(!q.empty()){
        int i=q.front();q.pop();auto p=tiles[i].get_position();++out.space;
        if(tiles[i].has_pearl()&&std::find(s.eaten.begin(),s.eaten.end(),p)==s.eaten.end())out.pearl_distance=std::min(out.pearl_distance,dist[i]);
        for(auto d:Direction::get_direction_list()){
            Position n;if(!m.destination(ct,p,d,n))continue;auto t=ct.get_tile(n);
            if(!t){out.frontier_distance=std::min(out.frontier_distance,dist[i]+1);continue;}
            int j=t-tiles.data();if(blocked[j])continue;if(i==start)++out.exits;
            if(dist[j]>=0)continue;dist[j]=dist[i]+1;q.push(j);
        }
    }return out;
}
}
