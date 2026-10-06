#ifdef CAPITAL_V2
#include "../opponents/generalist-v2/planner.hpp"
#else
#include "../opponents/generalist-v3/planner.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    // Exact observed r86 Portals-B local terrain/body/pearls. Historical
    // Atlas/traffic is unavailable; this is a current-observation replay.
    Game board{32,16,64};Controller bot{1,Team::B,Direction::WEST,Vision{},64};
    game=&board;ct=&bot;bot.head.position={28,1};bot.length=3;bot.unit_count=3;
    std::vector<Tile> tiles;
    for(int row=0;row<7;++row)for(int x=25;x<=31;++x)
        tiles.emplace_back(Position{x,(14+row)%16},std::nullopt,-1);
    bot.vision=Vision{std::move(tiles)};
    const char* h[]={".ww....",".......","wwwwwww","..67...",".ww....",".......",".ww....",".ww...."};
    const char* v[]={"..0....w",".......w",".w.w...w",".w.w...w",".......w",".......w",".w.w...w"};
    auto edge=[](char c,bool horizontal){return c=='.'?Edge{horizontal,EdgeType::EMPTY}:
        (c=='w'?Edge{horizontal,EdgeType::KELP}:Edge{horizontal,EdgeType::PORTAL,c-'0'});};
    for(int row=0;row<7;++row)for(int col=0;col<7;++col) {
        auto* t=bot.get_tile({25+col,(14+row)%16});
        t->get_edge(Direction::NORTH)=edge(h[row][col],true);
        t->get_edge(Direction::SOUTH)=edge(h[row+1][col],true);
        t->get_edge(Direction::WEST)=edge(v[row][col],false);
        t->get_edge(Direction::EAST)=edge(v[row][col+1],false);
    }
    bot.get_tile({28,1})->dragon_part=bot.head;
    bot.get_tile({29,1})->dragon_part=DragonPart{{29,1},1,Team::B,Direction::WEST,false};
    bot.get_tile({29,2})->dragon_part=DragonPart{{29,2},1,Team::B,Direction::NORTH,false};
    bot.get_tile({27,2})->dragon_part=DragonPart{{27,2},5,Team::B,Direction::NORTH,true};
    bot.get_tile({27,3})->dragon_part=DragonPart{{27,3},5,Team::B,Direction::NORTH,false};
    bot.get_tile({26,3})->dragon_part=DragonPart{{26,3},5,Team::B,Direction::EAST,false};
    for(auto p:std::vector<Position>{{26,0},{27,0},{26,1},{27,1},{26,4},{27,4}})bot.get_tile(p)->pearl=true;
    strategy::Memory memory;memory.body={{28,1},{29,1},{29,2}};memory.observe_map(bot,86);
    planner::State state;state.old_length=3;state.last_food=0;
    auto free=planner::initial(bot,memory);assert(planner::step(bot,memory,free,Direction::SOUTH,false));
    auto proof=free;
    for(auto d:std::vector<Direction>{Direction::EAST,Direction::NORTH,Direction::NORTH,Direction::EAST,
        Direction::EAST,Direction::SOUTH,Direction::SOUTH,Direction::SOUTH})
        assert(planner::step(bot,memory,proof,d,false));
    assert(proof.length==3&&proof.eaten.empty());
    int budget=140;auto future=planner::continuation(bot,memory,free,{},0,8,budget);
    assert(future.depth==8&&future.next_free_food==0);
    std::vector<bool> imminent;auto risk=planner::risks(bot,memory,&imminent);
    assert(!imminent[memory.index({28,2})]);
    assert(risk[memory.index({28,2})]==0.35&&risk[memory.index({28,3})]==0);
    auto plan=planner::choose(bot,memory,state);
    std::cout<<plan.note<<"\n";
#ifdef CAPITAL_V2
    assert(plan.kind==planner::Kind::Move&&plan.paid==1&&plan.food==0);
#else
    assert(plan.kind==planner::Kind::Move&&plan.paid==0&&plan.food==0);
    assert(plan.moves.size()==1&&plan.moves[0]==Direction(Direction::SOUTH));
#endif
    std::cout<<"Real local free-S eight-step continuation and dry-capital choice passed\n";
}
