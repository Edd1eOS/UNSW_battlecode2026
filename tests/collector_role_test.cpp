#include "../opponents/v62-collector-roles/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    game=&board;ct=&bot;std::vector<Tile> tiles;
    for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y});
    bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=4;bot.unit_count=20;
    bot.get_tile({5,5})->dragon_part=bot.head;
    strategy::Memory memory;memory.body={{5,5},{4,5},{3,5},{2,5}};
    for(int x=2;x<=4;++x) bot.get_tile({x,5})->dragon_part=DragonPart{{x,5},2,Team::A,Direction::EAST,false};
    bot.get_tile({6,5})->pearl=true;memory.observe_map(bot,100);
    forage::State state;
    auto plan=forage::choose(bot,memory,state);
    assert(state.collector && plan.action.child_size==0 && !plan.moves.empty());
    bot.unit_count=2;plan=forage::choose(bot,memory,state);
    assert(state.collector && plan.action.child_size==2);
    std::cout<<"Collector grows when colony established; resumes expansion after population collapse.\n";
}
