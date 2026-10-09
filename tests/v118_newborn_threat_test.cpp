#ifdef WITHOUT_SPLIT
#include "../opponents/v117-food-aware-threat/forage.hpp"
#else
#include "../opponents/v118-newborn-threat/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game g{15,15,64};Controller c{0,Team::A,Direction::NORTH,Vision{},64};game=&g;ct=&c;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    c.vision=Vision{std::move(tiles)};c.head={Position{5,5},0,Team::A,Direction::NORTH,true};c.length=3;c.unit_count=5;
    for(int y=5;y<=7;++y)c.get_tile({5,y})->dragon_part=DragonPart{{5,y},0,Team::A,Direction::NORTH,y==5};
    for(int x=3;x<=6;++x)c.get_tile({x,4})->dragon_part=DragonPart{{x,4},8,Team::B,Direction::WEST,x==3};
    strategy::Memory m;m.observe(c);
    auto danger=forage::growth_danger(c,m);
#ifdef WITHOUT_SPLIT
    assert(danger[m.index({6,5})]==0);
#else
    assert(danger[m.index({6,5})]>=1); // Split 2: new head at (6,4), then S.
#endif
    std::cout<<"Same-round newborn attack from reversed tail checked.\n";
}
