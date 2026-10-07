#include "../opponents/generalist-certainty-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;

int main() {
    // A legal, full current 7x7 view with a 12-segment Queen. After its
    // three free E steps, one branch is immediately outside the current
    // view; another has exactly six known steps ending at a sealed leaf.
    // This is a controlled contract check, not a match or hidden input.
    Game board{15,15,64};
    Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    game=&board;ct=&bot;bot.head.position={5,5};bot.length=12;bot.unit_count=2;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y)for(int x=2;x<=8;++x) {
        tiles.emplace_back(Position{x,y},std::nullopt,-1);
        for(auto d:Direction::get_direction_list())
            tiles.back().get_edge(d)=Edge{true,EdgeType::KELP,-1};
    }
    bot.vision=Vision{std::move(tiles)};
    auto open=[&](Position a,Position b) {
        for(auto d:Direction::get_direction_list())if(a.add_dir(d)==b) {
            if(auto* t=bot.get_tile(a))t->get_edge(d)=Edge{true,EdgeType::EMPTY,-1};
            if(auto* t=bot.get_tile(b))t->get_edge(d.get_opposite())=Edge{true,EdgeType::EMPTY,-1};
            return;
        }
        assert(false);
    };
    strategy::Memory memory;
    memory.body={{5,5},{4,5},{3,5},{2,5},{2,6},{3,6},{4,6},{5,6},{5,7},{4,7},{3,7},{2,7}};
    bot.get_tile(memory.body.front())->dragon_part=bot.head;
    for(int i=1;i<static_cast<int>(memory.body.size());++i) {
        Direction toward=Direction::EAST;
        for(auto d:Direction::get_direction_list())
            if(memory.body[i].add_dir(d)==memory.body[i-1])toward=d;
        bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],0,Team::A,toward,false};
        open(memory.body[i],memory.body[i-1]);
    }
    open({5,5},{6,5});open({6,5},{7,5});open({7,5},{8,5});
    open({8,5},{9,5}); // unknown immediately from the simulated endpoint
    const std::vector<Position> path={{8,4},{8,3},{7,3},{6,3},{5,3},{4,3}};
    Position previous{8,5};
    for(auto p:path){open(previous,p);previous=p;}
    memory.observe_map(bot,30);
    auto simulated=planner::initial(bot,memory);
    for(int i=0;i<3;++i)assert(planner::step(bot,memory,simulated,Direction::EAST,false));
    assert(simulated.body.front()==Position(8,5));
    Position unknown;
    assert(memory.destination(bot,simulated.body.front(),Direction::EAST,unknown));
    assert(unknown==Position(9,5)&&!bot.get_tile(unknown));
    int budget=140;
    const auto future=planner::continuation(bot,memory,simulated,{},0,8,budget);
    assert(future.depth==6&&future.outside&&!future.portal&&!future.exhausted);
    assert(planner::future_grade(future,8)==2);
    // The six-step branch has no unknown exit: its endpoint is sealed
    // except for the occupied neck. The outside flag came from the other
    // branch, rather than describing this maximum-depth branch.
    for(auto p:path) {
        bool moved=false;
        for(auto d:Direction::get_direction_list()) {
            Position to;
            if(memory.destination(bot,simulated.body.front(),d,to)&&to==p) {
                assert(planner::step(bot,memory,simulated,d,false));moved=true;break;
            }
        }
        assert(moved);
    }
    for(auto d:Direction::get_direction_list()) {
        auto next=simulated;
        assert(!planner::step(bot,memory,next,d,false));
        Position to;
        if(memory.destination(bot,simulated.body.front(),d,to))assert(bot.get_tile(to));
    }
    std::cout<<"Future maxdepth6 + outside from separate unknown0 branch PASS\n";
}
