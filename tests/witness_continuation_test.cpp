#include "../opponents/generalist-continuation-witness-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};Controller bot{0,Team::A,Direction::NORTH,Vision{},64};strategy::Memory memory;
    Scene() {
        game=&board;ct=&bot;bot.head.position={5,5};bot.length=2;bot.unit_count=4;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        for(auto& t:bot.vision.tiles)for(auto d:Direction::get_direction_list())
            t.get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::KELP,-1};
        bot.get_tile({5,5})->dragon_part=bot.head;
        bot.get_tile({5,6})->dragon_part=DragonPart{{5,6},0,Team::A,Direction::NORTH,false};
        memory.body={{5,5},{5,6}};
    }
    void edge(Position from,Direction d,EdgeType type=EdgeType::EMPTY,int portal=-1) {
        bot.get_tile(from)->get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),type,portal};
        Position to=from.add_dir(d);
        if(auto* t=bot.get_tile(to))t->get_edge(d.get_opposite())=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),type,portal};
    }
    void refresh(){memory.observe_map(bot,40);}
    planner::Future future(Position head,Position neck,int budget=300,int horizon=8) {
        refresh();strategy::Simulation s{{head,neck},{},true,2};
        return planner::continuation(bot,memory,s,{},0,horizon,budget);
    }
};
int main() {
    {
        Scene s;s.edge({2,5},Direction::WEST);s.edge({2,5},Direction::NORTH);
        for(int x=2;x<7;++x)s.edge({x,4},Direction::EAST);
        auto f=s.future({2,5},{2,6});
        assert(f.depth==6&&f.outside&&f.unresolved_depth==0);
        assert(planner::future_grade(f,8)==2);
        // The six-step finite branch did not become a six-step unknown witness.
    }
    {
        Scene s;
        for(int x=5;x>2;--x)s.edge({x,5},Direction::WEST);
        s.edge({2,5},Direction::WEST);
        auto f=s.future({5,5},{5,6});
        assert(f.depth==3&&f.outside&&f.unresolved_depth==3);
        // The unknown fourth step was never simulated or counted.
    }
    {
        Scene s;s.edge({5,5},Direction::NORTH);s.edge({5,4},Direction::NORTH);
        s.edge({5,3},Direction::EAST,EdgeType::PORTAL,7);
        auto f=s.future({5,5},{5,6});
        assert(f.depth==2&&f.portal&&f.unresolved_depth==2);
    }
    {
        Scene s;s.edge({5,5},Direction::NORTH);s.edge({5,4},Direction::NORTH);
        auto f=s.future({5,5},{5,6},1);
        assert(f.depth==1&&f.exhausted&&f.unresolved_depth==1);
        assert(f.depth<8); // Budget exhaustion never supplies the horizon.
    }
    {
        Scene s;
        for(int x=3;x<7;++x)s.edge({x,3},Direction::EAST);
        for(int y=3;y<7;++y)s.edge({7,y},Direction::SOUTH);
        for(int x=7;x>3;--x)s.edge({x,7},Direction::WEST);
        for(int y=7;y>3;--y)s.edge({3,y},Direction::NORTH);
        auto f=s.future({3,3},{3,4});
        assert(f.depth==8&&planner::future_grade(f,8)==3&&f.unresolved_depth==-1);
        assert(planner::unresolved_rank(f,true,3)==-1);
    }
    {
        planner::Future near{6,true,false,false,0,0},far{3,true,false,false,0,3};
        assert(planner::unresolved_rank(far,true,2)>planner::unresolved_rank(near,true,2));
        assert(planner::unresolved_rank(far,false,2)==planner::unresolved_rank(near,false,2));
        assert(planner::unresolved_rank(far,true,1)==-1&&planner::unresolved_rank(far,true,0)==-1);
        // Ordinary workers and confirmed horizon/finite grades keep old ordering.
    }
    std::cout<<"Continuation witness: mixed finite, outside, portal, budget, horizon and worker PASS\n";
}
