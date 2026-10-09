#ifdef PREVIOUS_MODEL
#include "../opponents/v118-newborn-threat/forage.hpp"
#else
#include "../opponents/v119-queen-body-threat/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game g{64,64,64}; Controller c{1,Team::A,Direction::SOUTH,Vision{},64}; game=&g; ct=&c;
    std::vector<Tile> tiles;
    for(int y=20;y<=26;++y)for(int x=31;x<=37;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    c.vision=Vision{std::move(tiles)};c.head={Position{34,23},1,Team::A,Direction::SOUTH,true};c.length=4;c.unit_count=25;
    c.get_tile({34,23})->dragon_part=DragonPart{{34,23},1,Team::A,Direction::SOUTH,true};
    c.get_tile({34,22})->dragon_part=DragonPart{{34,22},1,Team::A,Direction::SOUTH,false};
    for(int x=32;x<=33;++x)c.get_tile({x,22})->dragon_part=DragonPart{{x,22},1,Team::A,Direction::EAST,false};
    for(int x=34;x<=36;++x)c.get_tile({x,20})->dragon_part=DragonPart{{x,20},60,Team::B,Direction::WEST,x==34};
    strategy::Memory m;m.observe(c);auto danger=forage::growth_danger(c,m);
#ifdef PREVIOUS_MODEL
    assert(danger[m.index({34,22})]==0);
#else
    assert(danger[m.index({34,22})]>=0.8);
#endif
    std::cout<<"Queen old-body target on uncertain enemy tail checked.\n";
}
