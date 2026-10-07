#include "../opponents/generalist-certainty-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    // Controlled public observation: N is a permanent one-cell-wide leaf
    // with only two continuation steps; E has full continuation but possible
    // same-round reversed-tail child contact. This is not a recorded match.
    Game board{15,15,64};Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    game=&board;ct=&bot;bot.head.position={5,5};bot.length=2;bot.unit_count=4;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    bot.vision=Vision{std::move(tiles)};bot.get_tile({5,5})->dragon_part=bot.head;
    bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},0,Team::A,Direction::EAST,false};
    for(int y=2;y<=4;++y) {
        bot.get_tile({5,y})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
        bot.get_tile({6,y})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
        bot.get_tile({5,y})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
        bot.get_tile({4,y})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
    }
    bot.get_tile({5,2})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
    bot.get_tile({5,5})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
    bot.get_tile({5,6})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
    const std::vector<Position> enemy={{8,3},{8,4},{7,4},{7,5}};
    const std::vector<Direction> dirs={Direction::NORTH,Direction::NORTH,Direction::EAST,Direction::NORTH};
    for(int i=0;i<4;++i)bot.get_tile(enemy[i])->dragon_part=DragonPart{enemy[i],3,Team::B,dirs[i],i==0};
    strategy::Memory memory;memory.body={{5,5},{4,5}};memory.observe_map(bot,30);
    planner::State state;auto north=planner::initial(bot,memory),east=north;
    assert(planner::step(bot,memory,north,Direction::NORTH,false));
    assert(planner::step(bot,memory,east,Direction::EAST,false));
    int nb=140,eb=140;
    auto nf=planner::continuation(bot,memory,north,{},0,8,nb);
    auto ef=planner::continuation(bot,memory,east,{},0,8,eb);
    assert(nf.depth==2&&!nf.outside&&!nf.portal&&!nf.exhausted&&ef.depth==8);
#ifndef CLOSED_BIRTH_V3
    auto threats=born_threat::build(bot,memory);
    assert(threats.same_round_possible[memory.index({6,5})]);
    assert(!threats.same_round_possible[memory.index({5,4})]);
#endif
    auto plan=planner::choose(bot,memory,state);std::cout<<plan.note<<"\n";
#ifdef CLOSED_BIRTH_V3
    assert(plan.moves.front()==Direction(Direction::EAST));
#else
    assert(plan.moves.front()==Direction(Direction::EAST));
#endif
    std::cout<<"Birth tier versus finite closed route policy reproduced\n";
}
