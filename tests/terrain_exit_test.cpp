#ifdef CURRENT_BOT
#include "../bot/forage.hpp"
#elif defined(OLD_BASELINE)
#include "../opponents/v35-colony-economy/forage.hpp"
#else
#include "../opponents/v60-terrain-exits/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Corridor {
    Game board{20,20,64};
    Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Corridor() {
        game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=0;y<20;++y) for(int x=0;x<20;++x) {
            tiles.emplace_back(Position{x,y});
            for(auto d:Direction::get_direction_list()) tiles.back().get_edge(d).edge_type=EdgeType::KELP;
        }
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=3;bot.unit_count=64;
        memory.body={{5,5},{4,5},{3,5}};
        bot.get_tile({5,5})->dragon_part=bot.head;
        for(int x=3;x<=4;++x) bot.get_tile({x,5})->dragon_part=DragonPart{{x,5},2,Team::A,Direction::EAST,false};
        for(int x=3;x<14;++x) open({x,5},Direction::EAST);
        for(int x=3;x<5;++x) open({x,6},Direction::EAST);
        open({3,5},Direction::SOUTH);open({5,5},Direction::SOUTH);
        bot.get_tile({9,5})->pearl=true;
        memory.observe_map(bot,100);
    }
    void open(Position p,Direction d) {
        bot.get_tile(p)->get_edge(d).edge_type=EdgeType::EMPTY;
        bot.get_tile(p.add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::EMPTY;
    }
};
int main() {
    Corridor c;forage::State state;
    const auto plan=forage::choose(c.bot,c.memory,state);
#ifdef OLD_BASELINE
    assert(plan.moves.front()==Direction(Direction::EAST));
    std::cout<<"Baseline enters a terminal corridor beyond its six-step horizon.\n";
#else
    assert(plan.moves.front()==Direction(Direction::SOUTH));
    auto exits=terrain::build(c.bot,c.memory);
    assert(exits.worsens(c.memory,{5,5},{6,5}));
    assert(!exits.worsens(c.memory,{8,5},{7,5}));
    // An unresolved portal at the end is uncertain, not a proved terminal branch.
    c.bot.get_tile({14,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,73};
    c.memory.observe_map(c.bot,101);exits=terrain::build(c.bot,c.memory);
    assert(!exits.worsens(c.memory,{5,5},{6,5}));
    std::cout<<"Terminal corridor rejected; retreat and unresolved portal remain possible.\n";
#endif
}
