#include "../opponents/colony-lifecycle-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};Controller bot{8,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory m;planner::State state;
    Scene(){game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=4;bot.unit_count=40;
        m.body={{5,5},{4,5},{3,5},{2,5}};
        for(auto p:m.body)bot.get_tile(p)->dragon_part=DragonPart{p,8,Team::A,Direction::EAST,p==Position(5,5)};
        m.observe_map(bot,20);}
};
int main(){
    {Scene s;auto plan=planner::choose(s.bot,s.m,s.state);
        assert(plan.action.child_size==2); // Still expands above the former 24 cap.
        assert(action_evidence::audit(s.bot,s.m,{},2).status==action_evidence::Status::Confirmed);
        assert(!s.state.reserve);}
    {Scene s;for(auto d:Direction::get_direction_list())s.bot.get_tile({2,5})->get_edge(d)=Edge{false,EdgeType::KELP,-1};
        s.m.observe_map(s.bot,20);auto plan=planner::choose(s.bot,s.m,s.state);
        assert(plan.action.child_size==0); // Legal split alone cannot justify a trapped child.
        assert(!plan.moves.empty());}
    {Scene s;s.bot.unit_count=64;auto plan=planner::choose(s.bot,s.m,s.state);assert(plan.action.child_size==0);}
    {Scene s;s.m.now=499;auto plan=planner::choose(s.bot,s.m,s.state);assert(plan.action.child_size==0);}
    {Scene s;s.bot.length=8;colony::Lease lease;colony::update(s.bot,20,lease);assert(lease.champion);
        for(int x=2;x<=8;++x)s.bot.get_tile({x,2})->dragon_part=DragonPart{{x,2},4,Team::A,Direction::EAST,x==8};
        s.bot.get_tile({8,3})->dragon_part=DragonPart{{8,3},4,Team::A,Direction::NORTH,false};
        colony::update(s.bot,21,lease);assert(!lease.champion&&lease.dominant_id==4);
        for(auto& tile:s.bot.vision.tiles)if(tile.dragon_part&&tile.dragon_part->get_id()==4)tile.dragon_part.reset();
        colony::update(s.bot,25,lease);assert(!lease.champion);
        colony::update(s.bot,28,lease);assert(lease.champion&&lease.dominant_id<0);}
    std::cout<<"Colony: expansion at length4/population40, child trap rejection, hard cap, terminal horizon, champion demotion and expiry passed\n";
}
