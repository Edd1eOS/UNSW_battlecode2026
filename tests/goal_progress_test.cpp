#include "../opponents/v63-progress-targets/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    game=&board;ct=&bot;std::vector<Tile> tiles;
    for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y},std::nullopt,-1);
    bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=2;bot.unit_count=5;
    bot.get_tile({5,5})->dragon_part=bot.head;
    bot.get_tile({8,5})->pearl=true;bot.get_tile({2,8})->pearl=true;
    strategy::Memory memory;memory.body={{5,5},{4,5}};memory.observe_map(bot,100);
    forage::State state;auto exits=terrain::build(bot,memory);
    const int first=forage::select_goal(bot,memory,state,&exits);
    assert(first==memory.index({8,5}));
    // A loop has made no distance progress for eleven rounds.
    memory.observe_map(bot,111);
    const int alternative=forage::select_goal(bot,memory,state,&exits);
    assert(alternative==memory.index({2,8}) && state.cooling_goal==first);
    memory.observe_map(bot,112);
    assert(forage::select_goal(bot,memory,state,&exits)!=first);
    std::cout<<"Stalled goal cools down while another food target remains available.\n";
}
