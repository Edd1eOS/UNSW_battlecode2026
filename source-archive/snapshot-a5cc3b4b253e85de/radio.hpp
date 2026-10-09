#pragma once
#include "strategy.hpp"
namespace radio {
using namespace strategy;
struct Sighting {Position p;int seen=-1000;};
inline uint64_t tag(const Controller& ct){return 0xC826A0ULL+(ct.get_team()==unswbc::Team('A')?0:1);}
inline uint64_t checksum(uint64_t data){return (data^(data>>13)^(data>>27)^0x2D7ULL)&1023;}
inline void update(const Controller& ct,const Memory& m,Sighting& s,bool network){
    if(network)for(auto word:ct.get_sonar_messages()){
        if(word>>40!=tag(ct))continue;
        uint64_t data=(word>>10)&((1ULL<<30)-1);if((word&1023)!=checksum(data))continue;
        int seen=(data>>20)&1023,x=(data>>10)&1023,y=data&1023;
        if(seen>m.now||seen<m.now-6||seen<s.seen||x>=m.width||y>=m.height)continue;
        s={{x,y},seen};
    }
    if(s.seen>=m.now-6){
        const auto* t=ct.get_tile(s.p);const auto* p=t?t->get_dragon():nullptr;
        if(t&&(!p||!p->is_head()||p->get_id()>1||p->get_team()==ct.get_team()))s.seen=-1000;
    }
    for(const auto& t:ct.get_tiles())if(auto p=t.get_dragon())
        if(p->is_head()&&p->get_id()<=1&&p->get_team()!=ct.get_team())s={t.get_position(),m.now};
}
inline void send(const Controller& ct,const Memory& m,const Sighting& s){
    if(s.seen<m.now-6)return;
    uint64_t data=(uint64_t(s.seen)<<20)|(uint64_t(s.p.x)<<10)|uint64_t(s.p.y);
    uint64_t word=(tag(ct)<<40)|(data<<10)|checksum(data);
    std::cout<<"PROTOCOL 3\n";
    for(auto d:Direction::get_direction_list())ct.send_sonar(d,word);
}
}
