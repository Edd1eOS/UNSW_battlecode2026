#include "../opponents/generalist-v3/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    game=&board;ct=&bot;bot.head.position={5,5};bot.length=6;bot.unit_count=10;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
    bot.vision=Vision{std::move(tiles)};
    strategy::Memory memory;memory.body={{5,5},{4,5},{3,5},{3,6},{4,6},{5,6}};
    const std::vector<Direction> facing={Direction::EAST,Direction::EAST,Direction::EAST,
        Direction::NORTH,Direction::WEST,Direction::WEST};
    for(int i=0;i<6;++i)bot.get_tile(memory.body[i])->dragon_part=
        DragonPart{memory.body[i],2,Team::A,facing[i],i==0};
    memory.observe_map(bot,30);planner::State state;
    auto graph=planner::goals(bot,memory,state);
    const int desired=std::min(bot.unit_limit,std::min(24,std::max(4,graph.food_sites/2+graph.frontiers/6)));
    assert(graph.food_sites==0&&desired==4);
    auto parent=planner::initial(bot,memory);parent.body.resize(4);parent.length=4;
    strategy::Simulation child{{{5,6},{4,6}},{},true,2};
    int parentBudget=90,childBudget=90;
    auto pf=planner::continuation(bot,memory,parent,{{5,6},{4,6}},0,6,parentBudget);
    auto cf=planner::continuation(bot,memory,child,{{5,5},{4,5},{3,5},{3,6}},0,6,childBudget);
    assert(pf.depth==6&&cf.depth==6); // Both post-split bodies have legal continuation.
    auto plan=planner::choose(bot,memory,state);
    assert(!state.reserve&&plan.kind!=planner::Kind::Split);
    std::cout<<"same local capacity, units10: desired4 forbids ordinary investment\n";
    bot.unit_count=2;state=planner::State{};
    plan=planner::choose(bot,memory,state);assert(plan.kind==planner::Kind::Split);
    std::cout<<"same bodies and terrain, units2: split2 selected\n";
    // The grown-worker gate is independently unconditional once the role is
    // assigned, regardless of food sites or available regional capacity.
    bot.unit_count=3;bot.length=8;state=planner::State{};
    memory.body.push_back({5,7});memory.body.push_back({4,7});
    bot.get_tile({5,7})->dragon_part=DragonPart{{5,7},2,Team::A,Direction::NORTH,false};
    bot.get_tile({4,7})->dragon_part=DragonPart{{4,7},2,Team::A,Direction::EAST,false};
    planner::update_role(bot,memory,state);assert(state.reserve);
    bot.unit_count=20;planner::update_role(bot,memory,state);assert(state.reserve);
    std::cout<<"L8/unit3 sticky role persists; this is a policy gate, not legality\n";
}
