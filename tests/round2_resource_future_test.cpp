#include "../opponents/generalist-resource-priority-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};strategy::Memory m;
    Scene(){game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){Tile t(Position{x,y},std::nullopt,-1);
            for(auto d:Direction::get_direction_list())t.get_edge(d)=Edge{false,EdgeType::KELP,-1};tiles.push_back(t);}
        bot.vision=Vision{std::move(tiles)};bot.head.position={4,5};bot.length=4;bot.unit_count=3;
        m.body={{4,5},{3,5},{2,5},{2,6}};
        for(auto p:m.body)bot.get_tile(p)->dragon_part=DragonPart{p,2,Team::A,Direction::EAST,p==Position(4,5)};
        for(int x=4;x<8;++x){bot.get_tile({x,5})->get_edge(Direction::EAST)=Edge{};bot.get_tile({x+1,5})->get_edge(Direction::WEST)=Edge{};}
        bot.get_tile({5,5})->pearl=true;bot.get_tile({6,5})->pearl=true;m.observe_map(bot,100);}
};
int main(){
    Scene s;resource_priority::Field f;f.opportunity_cost.assign(s.m.cells.size(),0);
    f.opportunity_cost[s.m.index({5,5})]=65;f.opportunity_cost[s.m.index({6,5})]=45;
    auto sim=planner::initial(s.bot,s.m);int budget=90;
    auto a=planner::continuation(s.bot,s.m,sim,{},0,3,budget,-1,-1,0,&f);
    // L4 has one next-turn free step. Later pearl is not part of that reward.
    assert(a.depth==3&&a.next_free_food==1&&a.next_priority_cost==65);
    // A pearl already harvested by the current action must not be charged again.
    assert(planner::step(s.bot,s.m,sim,Direction::EAST,false));budget=90;
    a=planner::continuation(s.bot,s.m,sim,{},0,2,budget,-1,-1,0,&f);
    assert(a.next_free_food==1&&a.next_priority_cost==45);
    budget=90;auto unmarked=planner::continuation(s.bot,s.m,sim,{},0,2,budget);
    assert(unmarked.next_free_food==1&&unmarked.next_priority_cost==0);
    // Equal-depth finite branches retain the food and cost of the same branch.
    Scene branch;branch.bot.get_tile({6,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
    branch.bot.get_tile({4,5})->get_edge(Direction::NORTH)=Edge{};
    branch.bot.get_tile({4,4})->get_edge(Direction::SOUTH)=Edge{};
    branch.bot.get_tile({4,4})->get_edge(Direction::NORTH)=Edge{};
    branch.bot.get_tile({4,3})->get_edge(Direction::SOUTH)=Edge{};
    branch.bot.get_tile({4,4})->pearl=true;branch.m.observe_map(branch.bot,100);
    f.opportunity_cost[branch.m.index({4,4})]=65;f.opportunity_cost[branch.m.index({5,5})]=45;
    sim=planner::initial(branch.bot,branch.m);budget=90;
    a=planner::continuation(branch.bot,branch.m,sim,{},0,4,budget,-1,-1,0,&f);
    assert(a.depth==2&&a.next_free_food==1&&a.next_priority_cost==45);
    std::cout<<"Future priority: same witness, fixed free window, no double charge of current food, unmarked behavior preserved\n";
}
