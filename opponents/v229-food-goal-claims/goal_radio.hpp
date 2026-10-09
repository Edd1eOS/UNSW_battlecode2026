#pragma once
#include "strategy.hpp"
namespace goal_radio {
using namespace strategy;
struct Claim { int id,round; Position head,goal; };
struct Claims { std::vector<Claim> items; };
inline uint64_t checksum(uint64_t w){ return (w^(w>>8)^(w>>16)^(w>>24)^(w>>32)^(w>>40)^(w>>48))&255; }
inline void receive(const Controller& ct,const Memory& m,Claims& claims){
    auto& items=claims.items;
    items.erase(std::remove_if(items.begin(),items.end(),[&](const Claim& c){return m.now-c.round>3;}),items.end());
    int scanned=0;
    for(uint64_t word:ct.get_sonar_messages()){
        if(++scanned>256)break;
        uint64_t data=word&((1ULL<<56)-1);
        if((word>>56)!=checksum(data) || ((data>>46)&1023)!=669)continue;
        if(((data>>45)&1)!=(ct.get_team()==unswbc::Team('B')))continue;
        Claim c{int((data>>33)&4095),int((data>>24)&511),{int((data>>12)&63),int((data>>18)&63)},{int(data&63),int((data>>6)&63)}};
        if(c.id==ct.get_id() || c.round>m.now || m.now-c.round>3 || c.goal.x>=m.width || c.goal.y>=m.height || c.head.x>=m.width || c.head.y>=m.height)continue;
        auto it=std::find_if(items.begin(),items.end(),[&](const Claim& old){return old.id==c.id;});
        if(it!=items.end()){if(c.round>=it->round)*it=c;}else if(items.size()<64)items.push_back(c);
    }
}
inline void send(Controller& ct,const Memory& m,int goal){
    if(goal<0 || goal>=(int)m.cells.size() || ct.get_id()>4095 || m.now>511 || m.body.empty())return;
    Position g{goal%m.width,goal/m.width},h=m.body.front();
    if(g.x>=64||g.y>=64||h.x>=64||h.y>=64)return;
    uint64_t data=uint64_t(g.x)|(uint64_t(g.y)<<6)|(uint64_t(h.x)<<12)|(uint64_t(h.y)<<18)|(uint64_t(m.now)<<24)|(uint64_t(ct.get_id())<<33)|(uint64_t(ct.get_team()==unswbc::Team('B'))<<45)|(669ULL<<46);
    uint64_t word=data|(checksum(data)<<56);
    std::cout<<"PROTOCOL 3\n";
    for(auto d:Direction::get_direction_list())ct.send_sonar(d,word);
}
}
