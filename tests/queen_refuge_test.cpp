#ifdef CURRENT_BOT
#include "../bot/forage.hpp"
#elif defined(OLD_BASELINE)
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v99-queen-refuge/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{20,15,64};
    Controller queen{0,Team::A,Direction::NORTH,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game=&board;ct=&queen;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};
        queen.length=4;queen.unit_count=4;
        memory.body={{5,5},{5,6},{5,7},{5,8}};
        place_body();
    }
    void place_body() {
        for(auto& tile:queen.vision.tiles) tile.dragon_part.reset();
        queen.get_tile(queen.get_position())->dragon_part=queen.head;
        for(int i=1;i<static_cast<int>(memory.body.size());++i)
            if(auto* tile=queen.get_tile(memory.body[i])) tile->dragon_part=
                DragonPart{memory.body[i],queen.get_id(),Team::A,queen.get_dir(),false};
    }
    void enemy(int id,Position head,Position tail,Direction dir) {
        queen.get_tile(head)->dragon_part=DragonPart{head,id,Team::B,dir,true};
        queen.get_tile(tail)->dragon_part=DragonPart{tail,id,Team::B,dir,false};
    }
    void observe(int round=40) {memory.observe_map(queen,round);}
    Position finish(const forage::Plan& plan) {
        strategy::Simulation next{memory.body,{},true,queen.length};
        const int free_steps=(queen.length+3)/4;
        for(int i=0;i<static_cast<int>(plan.moves.size());++i) {
            assert(strategy::simulate_step(queen,next,plan.moves[i],&memory));
            if(i>=free_steps) {--next.length;if(static_cast<int>(next.body.size())>next.length) next.body.pop_back();}
        }
        return next.body.front();
    }
    forage::State anchored(Position anchor,int dry_since=40) {
        forage::State state;
#ifndef OLD_BASELINE
        state.queen_anchor=memory.index(anchor);state.queen_dry_since=dry_since;
#else
        (void)anchor;(void)dry_since;
#endif
        return state;
    }
};

int main() {
    // Food in the old area takes priority over a more distant excursion.
    {
        Scene s;s.queen.get_tile({4,5})->pearl=true;
        s.queen.get_tile({8,5})->pearl=true;s.observe();
        auto state=s.anchored({1,5});auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(4,5));
        assert(plan.moves.size()==1 && plan.action.child_size==0);
    }
    // A pearl one step beyond the radius still permits immediate safe growth.
    {
        Scene s;s.queen.get_tile({6,5})->pearl=true;s.observe();
        auto state=s.anchored({1,5});auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(6,5));assert(plan.moves.size()==1);
    }
    // With an empty interior, v66 immediately follows a distant pearl outside
    // the old radius. v99 first returns inward, letting its dry timer expand.
    {
        Scene s;s.queen.get_tile({8,5})->pearl=true;s.observe();
        auto state=s.anchored({1,5});auto plan=forage::choose(s.queen,s.memory,state);
#ifdef OLD_BASELINE
        assert(s.finish(plan)==Position(6,5));
#else
        assert(s.finish(plan)==Position(4,5));assert(state.queen_radius==4);
#endif
    }
    // Twelve dry rounds expand the radius by two. Migration is then allowed.
    {
        Scene s;s.queen.get_tile({8,5})->pearl=true;s.observe(52);
        auto state=s.anchored({1,5},40);auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(6,5));assert(plan.moves.size()==1);
#ifndef OLD_BASELINE
        assert(state.queen_radius==6);
        assert(forage::distance(s.memory,{1,5},s.finish(plan))>4);
#endif
    }
    // Visible pursuit disables the preference, retaining v66's paid escape.
    {
        Scene s;s.queen.head.dir=Direction::EAST;
        s.memory.body={{5,5},{4,5},{3,5},{2,5}};s.place_body();
        s.enemy(3,{5,3},{6,3},Direction::WEST);
        s.enemy(5,{7,5},{7,4},Direction::SOUTH);
        s.enemy(7,{5,7},{4,7},Direction::EAST);s.observe();
        auto state=s.anchored({6,7});auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.moves.size()>=2 && plan.action.child_size==0);
        auto danger=forage::queen_danger(s.queen,s.memory);
        assert(danger[s.memory.index(s.finish(plan))]==0);
        assert(forage::distance(s.memory,{6,7},s.finish(plan))>4);
#ifndef OLD_BASELINE
        assert(forage::queen_under_pressure(s.queen));
#endif
    }
    // Worker movement still follows the distant food without any territory cost.
    {
        Scene s;s.queen.head.dragon_id=2;s.queen.unit_count=64;s.place_body();
        s.queen.get_tile({8,5})->pearl=true;s.observe();
        auto state=s.anchored({1,5});auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(6,5));assert(plan.moves.size()==1);
    }
#ifndef OLD_BASELINE
    // Net growth beyond the old radius, without visible enemies, establishes
    // a new productive area rather than pulling the Queen back indefinitely.
    {
        Scene s;s.queen.head.position={6,5};s.queen.length=5;
        s.memory.body={{6,5},{6,6},{6,7},{6,8},{6,9}};s.place_body();s.observe(60);
        auto state=s.anchored({1,5},40);state.old_length=4;
        forage::choose(s.queen,s.memory,state);
        assert(state.queen_anchor==s.memory.index({6,5}) && state.queen_radius==4);
        assert(state.queen_dry_since==60);
    }
#endif
    std::cout << "Queen territory: nearby growth, distant food restraint, dry-area migration and paid escape passed.\n";
}
