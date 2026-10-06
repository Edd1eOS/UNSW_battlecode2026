#ifdef CLOSED_ROUTE_V1
#include "../opponents/generalist-v1/planner.hpp"
#else
#include "../opponents/generalist-v2/planner.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game board{15,15,64};Controller bot{0,Team::A,Direction::NORTH,Vision{},64};
    game=&board;ct=&bot;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=3;bot.unit_count=4;
    strategy::Memory memory;memory.body={{5,5},{4,5},{3,5}};
    for(int i=0;i<3;++i)bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],0,Team::A,Direction::EAST,i==0};
    bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,42};
    bot.get_tile({5,5})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
    for(auto p:std::vector<Position>{{5,4},{5,3},{5,2}}) {
        bot.get_tile(p)->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
        bot.get_tile(p)->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
    }
    bot.get_tile({5,2})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
    bot.get_tile({5,4})->pearl=true;
    memory.observe_map(bot,30);planner::State state;
    auto sim=planner::initial(bot,memory);assert(planner::step(bot,memory,sim,Direction::NORTH,false));
    int budget=140;auto future=planner::continuation(bot,memory,sim,{},0,8,budget);
    assert(future.depth==2&&!future.outside&&!future.portal&&!future.exhausted);
    auto selected=planner::choose(bot,memory,state);
#ifdef CLOSED_ROUTE_V1
    assert(selected.kind==planner::Kind::Move&&selected.moves.front()==Direction(Direction::NORTH));
    std::cout<<"V1 reproduces finite frozen-occupancy route outranking unresolved exit\n";
#else
    assert(selected.kind==planner::Kind::UnknownPortal&&selected.moves.front()==Direction(Direction::EAST));
    std::cout<<"V2 prefers unresolved exit over exhausted finite route; unknown is not declared safe\n";
#endif
}
