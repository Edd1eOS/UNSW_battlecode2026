#include "../opponents/v117-food-aware-threat/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game g{15,15,64};Controller c{0,Team::A,Direction::NORTH,Vision{},64};game=&g;ct=&c;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    c.vision=Vision{std::move(tiles)};c.head={Position{5,5},0,Team::A,Direction::NORTH,true};c.length=3;c.unit_count=5;
    c.get_tile({5,5})->dragon_part=c.head;
    c.get_tile({5,6})->dragon_part=DragonPart{{5,6},0,Team::A,Direction::NORTH,false};
    c.get_tile({5,7})->dragon_part=DragonPart{{5,7},0,Team::A,Direction::NORTH,false};
    c.get_tile({3,4})->dragon_part=DragonPart{{3,4},8,Team::B,Direction::SOUTH,true};
    c.get_tile({3,3})->dragon_part=DragonPart{{3,3},8,Team::B,Direction::SOUTH,false};
    strategy::Memory m;m.observe(c);
    auto no_food=forage::growth_danger(c,m);
    assert(no_food[m.index({5,4})]==0); // Length two cannot pay for a second step.
    c.get_tile({4,4})->pearl=true;m.observe(c);
    auto old=forage::queen_danger(c,m),grown=forage::growth_danger(c,m);
    assert(old[m.index({5,4})]==0);
    assert(grown[m.index({5,4})]>=0.8); // Eat on free E, then pay for E.
    // A first-step wall prevents the pearl-funded two-step attack.
    c.get_tile({3,4})->get_edge(Direction::EAST).edge_type=EdgeType::KELP;
    c.get_tile({4,4})->get_edge(Direction::WEST).edge_type=EdgeType::KELP;m.observe(c);
    assert(forage::growth_danger(c,m)[m.index({5,4})]==0);
    std::cout<<"Length-two food-funded sprint detected; empty route and wall controls pass.\n";
}
