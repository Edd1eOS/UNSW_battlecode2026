#pragma once
#include "strategy.hpp"
namespace map_radio {
using namespace strategy;
inline uint64_t magic(const Controller& ct){return 0xBCA0ULL+(ct.get_team()==unswbc::Team('A')?0:1);}
inline uint64_t checksum(uint64_t x){return (x^(x>>17)^(x>>29)^0x5A3ULL)&4095;}
inline uint64_t encode(const Controller& ct,const unswbc::Tile& tile,int round){
    auto p=tile.get_position();if(p.x>=64||p.y>=64||round>511)return 0;
    uint64_t walls=0;int k=0;
    for(auto d:Direction::get_direction_list()){
        const auto e=tile.get_edge(d);if(e.is_portal())return 0;
        if(e.get_edge_type()==EdgeType::KELP)walls|=1ULL<<k;++k;
    }
    int timer=tile.get_pearl_time();timer=timer<0?1023:std::min(timer,1022);
    uint64_t data=(uint64_t(round)<<27)|(uint64_t(p.x)<<21)|(uint64_t(p.y)<<15)
        |(walls<<11)|(uint64_t(tile.has_pearl())<<10)|uint64_t(timer);
    return (magic(ct)<<48)|(data<<12)|checksum(data);
}
inline int receive(const Controller& ct,Memory& m){
    int accepted=0,scanned=0;
    for(auto word:ct.get_sonar_messages()){
        if(++scanned>256)break;if(word>>48!=magic(ct))continue;
        auto data=(word>>12)&((1ULL<<36)-1);if((word&4095)!=checksum(data))continue;
        int seen=(data>>27)&511,x=(data>>21)&63,y=(data>>15)&63;
        if(x>=m.width||y>=m.height||seen>m.now||seen<m.now-16)continue;
        auto& c=m.cells[y*m.width+x];if(c.seen>=seen)continue;
        c.known=true;c.seen=seen;c.pearl=(data>>10)&1;int timer=data&1023;
        c.spawn_round=timer==1023?-1:seen+timer;
        for(int k=0;k<4;++k)c.edges[k]=unswbc::Edge(k%2==0,((data>>(11+k))&1)?EdgeType::KELP:EdgeType::EMPTY);
        ++accepted;
    }return accepted;
}
inline void send(Controller& ct,const Memory& m){
    const auto& tiles=ct.get_tiles();if(tiles.empty())return;
    std::cout<<"PROTOCOL 3\n";
    int k=0;for(auto d:Direction::get_direction_list()){
        int begin=(m.now*17+ct.get_id()*11+k++*13)%tiles.size();
        for(int j=0;j<(int)tiles.size();++j){
            auto word=encode(ct,tiles[(begin+j)%tiles.size()],m.now);
            if(word){ct.send_sonar(d,word);break;}
        }
    }
}
}
