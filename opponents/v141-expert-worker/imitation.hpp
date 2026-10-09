#pragma once
#include "strategy.hpp"
#include "learned_weights.hpp"
namespace imitation {
using namespace strategy;
using Features=std::array<double,45>;
struct Local {
    const Controller& ct;const Memory& m;
    std::vector<Position> cells;
    std::vector<std::vector<int>> adj;
    std::vector<bool> frontier;
    std::vector<int> lookup;
    Local(const Controller& c,const Memory& mem):ct(c),m(mem),lookup(mem.cells.size(),-1) {
        for(const auto& t:ct.get_tiles()){lookup[m.index(t.get_position())]=cells.size();cells.push_back(t.get_position());}
        adj.resize(cells.size());frontier.resize(cells.size());
        for(int i=0;i<(int)cells.size();++i)for(auto d:Direction::get_direction_list()) {
            if(ct.get_tile(cells[i])->get_edge(d).get_edge_type()!=EdgeType::EMPTY)continue;
            auto p=cells[i].add_dir(d);int j=lookup[m.index(p)];
            if(j<0)frontier[i]=true;else adj[i].push_back(j);
        }
    }
    int distance(Position a,Position b) const {
        int dx=std::abs(a.x-b.x),dy=std::abs(a.y-b.y);
        return std::min(dx,m.width-dx)+std::min(dy,m.height-dy);
    }
    bool features(Direction d,Features& f) const {
        const auto* here=ct.get_tile(ct.get_position());
        if(here->get_edge(d).get_edge_type()!=EdgeType::EMPTY)return false;
        auto n=ct.get_position().add_dir(d);const auto* landing=ct.get_tile(n);
        if(!landing||landing->get_dragon())return false;
        int start=lookup[m.index(n)];std::vector<bool> occupied(cells.size());
        for(int i=0;i<(int)cells.size();++i)occupied[i]=ct.get_tile(cells[i])->get_dragon()!=nullptr;
        if(!landing->has_pearl() && (int)m.body.size()==ct.get_length()) {
            int tail=lookup[m.index(m.body.back())];if(tail>=0)occupied[tail]=false;
        }
        std::vector<int> dist(cells.size(),-1);std::queue<int> q;q.push(start);dist[start]=0;
        int space=0,foodcount=0,foodnear=10000,spawnnear=10000,frontnear=10000;double foodsum=0;
        while(!q.empty()) {
            int i=q.front();q.pop();++space;const auto* tile=ct.get_tile(cells[i]);
            if(tile->has_pearl()){++foodcount;foodnear=std::min(foodnear,dist[i]);foodsum+=1.0/(1+dist[i]);}
            if(tile->get_pearl_time()>=0)spawnnear=std::min(spawnnear,dist[i]+tile->get_pearl_time());
            if(frontier[i])frontnear=std::min(frontnear,dist[i]);
            for(int j:adj[i])if(!occupied[j]&&dist[j]<0){dist[j]=dist[i]+1;q.push(j);}
        }
        int enemyhead=10000,enemybody=10000,allyhead=10000,queen=10000,degree=0;
        for(int j:adj[start])if(!occupied[j])++degree;
        for(const auto& tile:ct.get_tiles()) {
            const auto* p=tile.get_dragon();if(!p)continue;
            int dd=distance(n,tile.get_position());
            if(p->get_team()!=ct.get_team()){
                enemybody=std::min(enemybody,dd);if(p->is_head())enemyhead=std::min(enemyhead,dd);
            } else if(p->is_head()&&p->get_id()!=ct.get_id()){
                allyhead=std::min(allyhead,dd);if(p->get_id()<2)queen=std::min(queen,dd);
            }
        }
        auto inv=[](int a){return a==10000?0.0:1.0/(1+a);};
        std::array<double,15> base={double(landing->has_pearl()),space/49.0,inv(foodnear),foodsum/5,foodcount/10.0,
          degree/4.0,inv(frontnear),inv(enemyhead),inv(enemybody),inv(allyhead),inv(queen),
          m.visits(n)/4.0,double(d==ct.get_dir()),inv(spawnnear),double(degree==0)};
        for(int i=0;i<15;++i){f[i]=base[i];f[i+15]=base[i]*std::min(ct.get_length(),16)/16;f[i+30]=base[i]*m.now/500.0;}
        return true;
    }
};
inline bool choose(const Controller& ct,const Memory& m,Direction& chosen) {
    if(ct.get_id()<2||ct.get_length()>6)return false;
    for(auto d:Direction::get_direction_list())if(ct.get_tile(ct.get_position())->get_edge(d).is_portal())return false;
    Local local(ct,m);int valid=0;double best=-1e30;
    for(auto d:Direction::get_direction_list()){
        Features f{};if(!local.features(d,f))continue;++valid;double score=0;
        for(int i=0;i<45;++i)score+=f[i]*WEIGHTS[i];
        if(score>best){best=score;chosen=d;}
    }
    return valid>=2;
}
}
