#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v102-queen-vision-buffer/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{25,25,64};
    Controller queen{1,Team::B,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Scene(int length=4) {
        game=&board;ct=&queen;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};
        queen.length=length;queen.unit_count=7;
        for(int i=0;i<length;++i) memory.body.push_back({(5-i+25)%25,5});
        place_body();
    }
    void place_body() {
        for(auto& tile:queen.vision.tiles) tile.dragon_part.reset();
        queen.get_tile(queen.get_position())->dragon_part=queen.head;
        for(int i=1;i<static_cast<int>(memory.body.size());++i) {
            Direction toward=Direction::EAST;
            for(auto d:Direction::get_direction_list())
                if(memory.body[i].add_dir(d)==memory.body[i-1]) toward=d;
            if(auto* tile=queen.get_tile(memory.body[i])) tile->dragon_part=
                DragonPart{memory.body[i],queen.get_id(),Team::B,toward,false};
        }
    }
    void enemy(int id,Position head,Position tail,Direction dir) {
        queen.get_tile(head)->dragon_part=DragonPart{head,id,Team::A,dir,true};
        queen.get_tile(tail)->dragon_part=DragonPart{tail,id,Team::A,dir,false};
    }
    void wall(Position p,Direction d) {
        queen.get_tile(p)->get_edge(d)=Edge{false,EdgeType::KELP};
        if(auto* next=queen.get_tile(p.add_dir(d)))
            next->get_edge(d.get_opposite())=Edge{false,EdgeType::KELP};
    }
    void enclose() {
        for(int n=2;n<=8;++n) {
            wall({n,2},Direction::NORTH);wall({n,8},Direction::SOUTH);
            wall({2,n},Direction::WEST);wall({8,n},Direction::EAST);
        }
    }
    void south_corridor() {
        if(memory.body[1]!=Position(5,4)) wall({5,5},Direction::NORTH);
        wall({5,5},Direction::EAST);
        for(int y=6;y<=7;++y) {
            wall({5,y},Direction::EAST);wall({5,y},Direction::WEST);
        }
    }
    void observe() {memory.observe_map(queen,46);}
    Position finish(const forage::Plan& plan) {
        strategy::Simulation next{memory.body,{},true,queen.length};
        const int free_steps=(queen.length+3)/4;
        for(int i=0;i<static_cast<int>(plan.moves.size());++i) {
            assert(strategy::simulate_step(queen,next,plan.moves[i],&memory));
            if(i>=free_steps) {--next.length;if(static_cast<int>(next.body.size())>next.length) next.body.pop_back();}
        }
        return next.body.front();
    }
};

int main() {
    // Trophy957659's causal geometry: a long Queen can end at dy=3 while an
    // unseen head at dy=4 can collide next. This is a constructed scene with
    // that geometry, not a claim to reproduce its full recorded observation.
    {
        Scene s(16);s.south_corridor();s.queen.get_tile({5,8})->pearl=true;s.observe();
        assert(!s.queen.get_tile({5,9}));
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
#ifdef OLD_BASELINE
        assert(s.finish(plan)==Position(5,8));
#else
        auto margin=forage::queen_vision_margin(s.queen,s.memory);
        assert(margin[s.memory.index({5,8})]==1);
        assert(s.finish(plan)==Position(5,6));
        assert(margin[s.memory.index(s.finish(plan))]>=3);
#endif
    }
    // An interior pearl at dy=2 can still provide growth without continuing
    // unnecessarily to the exposed edge after eating it.
    {
        Scene s(16);s.south_corridor();s.queen.get_tile({5,7})->pearl=true;s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(5,7));assert(plan.moves.size()==2);
    }
    // Kelp enclosing the visible room prevents unseen entry. Its edge pearl
    // remains safe to eat, so an axis-aligned distance alone would be wrong.
    {
        Scene s(12);
        s.memory.body={{5,5},{5,4},{4,4},{3,4},{2,4},{2,5},
                       {3,5},{4,5},{4,6},{3,6},{2,6},{2,7}};
        s.place_body();s.enclose();s.south_corridor();s.queen.get_tile({5,8})->pearl=true;s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(5,8));assert(plan.moves.size()==3);
#ifndef OLD_BASELINE
        auto margin=forage::queen_vision_margin(s.queen,s.memory);
        assert(margin[s.memory.index({5,8})]>=4);
#endif
    }
    // The only path out of three visible length-2 attacks ends at the boundary.
    // The 1800 immediate-danger penalty must outweigh the 600 boundary cost.
    {
        Scene s(8);
        s.enemy(8,{7,5},{7,4},Direction::SOUTH);
        s.enemy(10,{5,6},{4,6},Direction::EAST);
        s.enemy(12,{5,7},{4,7},Direction::EAST);
        s.wall({5,5},Direction::NORTH);s.wall({6,5},Direction::NORTH);
        s.wall({6,6},Direction::EAST);s.wall({6,7},Direction::EAST);s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        auto danger=forage::danger_map(s.queen,s.memory);
        assert(plan.moves.size()==4 && plan.action.child_size==0);
        assert(s.finish(plan)==Position(6,8));
        assert(danger[s.memory.index(s.finish(plan))]==0);
#ifndef OLD_BASELINE
        auto margin=forage::queen_vision_margin(s.queen,s.memory);
        assert(margin[s.memory.index(s.finish(plan))]==1);
#endif
    }
    // With no food or visible threats, a normal legal one-step move still wins.
    {
        Scene s;s.observe();forage::State state;
        auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.moves.size()==1 && plan.action.child_size==0);
        assert(s.finish(plan)!=s.queen.get_position());
    }
    // Workers retain the old appetite for a pearl at the view's edge.
    {
        Scene s(16);s.queen.head.dragon_id=3;s.queen.unit_count=64;s.place_body();
        s.south_corridor();s.queen.get_tile({5,8})->pearl=true;s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(5,8));assert(plan.moves.size()==3);
    }
#ifndef OLD_BASELINE
    // Unknown portal exits remain a possible unseen entry, even in a walled
    // room. Own body squares are allowed to vacate when propagating the margin.
    {
        Scene s;s.enclose();
        s.queen.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,42};
        s.observe();auto margin=forage::queen_vision_margin(s.queen,s.memory);
        assert(margin[s.memory.index({5,5})]==1);
        assert(margin[s.memory.index({4,5})]==2);
    }
#endif
    std::cout << "Queen visible-terrain boundary buffer, interior growth, kelp cover and mandatory paid edge escape passed.\n";
}
