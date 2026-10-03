#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v97-queen-survival/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller queen{0,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game=&board;ct=&queen;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};
        queen.length=4;queen.unit_count=4;
        memory.body={{5,5},{4,5},{3,5},{2,5}};
        queen.get_tile({5,5})->dragon_part=queen.head;
        for(int i=1;i<4;++i) queen.get_tile(memory.body[i])->dragon_part=
            DragonPart{memory.body[i],0,Team::A,Direction::EAST,false};
    }
    void enemy(int id,Position head,Position tail,Direction dir) {
        queen.get_tile(head)->dragon_part=DragonPart{head,id,Team::B,dir,true};
        queen.get_tile(tail)->dragon_part=DragonPart{tail,id,Team::B,dir,false};
    }
    void wall(Position p,Direction d) {
        queen.get_tile(p)->get_edge(d)=Edge{false,EdgeType::KELP};
        queen.get_tile(p.add_dir(d))->get_edge(d.get_opposite())=Edge{false,EdgeType::KELP};
    }
    void observe() {memory.observe_map(queen,40);}
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
    // The pearl sits just outside a length-2 attacker's current one-step reach.
    // Walls force its eater into a corridor with no free next-round refuge.
    {
        Scene s;s.enemy(3,{7,4},{7,3},Direction::SOUTH);
        s.queen.get_tile({6,5})->pearl=true;
        s.wall({6,5},Direction::NORTH);s.wall({6,5},Direction::SOUTH);s.observe();
        assert(forage::enemy_reach(s.queen,s.memory,*s.queen.get_tile({7,4}))==1);
        auto danger=forage::danger_map(s.queen,s.memory);
        assert(danger[s.memory.index({6,5})]==0);
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
#ifdef OLD_BASELINE
        assert(s.finish(plan)==Position(6,5));
#else
        auto forecast=forage::queen_forecast(s.queen,s.memory);
        assert(forecast[s.memory.index({6,5})]==1);
        strategy::Simulation eater{s.memory.body,{},true,s.queen.length};
        assert(strategy::simulate_step(s.queen,eater,Direction::EAST,&s.memory));
        auto exits=terrain::build(s.queen,s.memory);
        assert(!forage::queen_has_refuge(s.queen,s.memory,eater,forecast,exits));
        assert(forecast[s.memory.index(s.finish(plan))]==0);
        assert(plan.moves.size()==1);
#endif
    }
    // The same pearl is acceptable when a visible free escape is available.
    {
        Scene s;s.enemy(3,{7,4},{7,3},Direction::SOUTH);
        s.queen.get_tile({6,5})->pearl=true;s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(6,5));
        assert(plan.moves.size()==1 && plan.action.child_size==0);
    }
    // A nearby uncontested pearl still wins, preserving normal Queen growth.
    {
        Scene s;s.enemy(3,{7,4},{7,3},Direction::SOUTH);
        s.queen.get_tile({5,6})->pearl=true;s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(5,6));
        assert(plan.moves.size()==1);
    }
    // Immediate three-sided attacks must still trigger paid emergency movement.
    {
        Scene s;s.enemy(3,{5,3},{6,3},Direction::WEST);
        s.enemy(5,{7,5},{7,4},Direction::SOUTH);
        s.enemy(7,{5,7},{4,7},Direction::EAST);s.observe();
        auto danger=forage::queen_danger(s.queen,s.memory);
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.moves.size()>=2 && plan.action.child_size==0);
        assert(danger[s.memory.index(s.finish(plan))]==0);
        strategy::remember_action(s.queen,s.memory,plan.action,plan.moves,40);
        assert(s.memory.body.size()==4-(plan.moves.size()-1));
    }
    // Normal colony seeding holds the Queen still. Do not seed under a visible
    // pursuer's forecast, even when that head is not an adjacent threat yet.
    {
        Scene s;
        for(auto& tile:s.queen.vision.tiles) tile.dragon_part.reset();
        s.memory.body={{5,5},{4,5},{3,5},{2,5},{2,6},{3,6},
                       {4,6},{4,7},{3,7},{2,7},{2,8}};
        s.queen.length=11;s.queen.unit_count=1;
        s.queen.get_tile({5,5})->dragon_part=s.queen.head;
        for(int i=1;i<11;++i) {
            Direction toward=Direction::NORTH;
            for(auto d:Direction::get_direction_list())
                if(s.memory.body[i].add_dir(d)==s.memory.body[i-1]) toward=d;
            s.queen.get_tile(s.memory.body[i])->dragon_part=
                DragonPart{s.memory.body[i],0,Team::A,toward,false};
        }
        s.enemy(3,{5,3},{6,3},Direction::WEST);s.observe();
        assert(strategy::nearby_threats(s.queen,s.queen.get_position())==0);
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
#ifdef OLD_BASELINE
        assert(plan.action.child_size==3);
#else
        assert(forage::queen_forecast(s.queen,s.memory)[s.memory.index({5,5})]==1);
        assert(plan.action.child_size==0 && !plan.moves.empty());
#endif
    }
    // Worker harvesting remains unchanged by the Queen-only forecast.
    {
        Scene s;s.queen.head.dragon_id=2;s.queen.unit_count=64;
        for(auto p:s.memory.body) s.queen.get_tile(p)->dragon_part->dragon_id=2;
        s.enemy(3,{7,4},{7,3},Direction::SOUTH);
        s.queen.get_tile({6,5})->pearl=true;
        s.wall({6,5},Direction::NORTH);s.wall({6,5},Direction::SOUTH);s.observe();
        forage::State state;auto plan=forage::choose(s.queen,s.memory,state);
        assert(s.finish(plan)==Position(6,5));
        assert(plan.moves.size()==1 && plan.action.child_size==0);
    }
#ifndef OLD_BASELINE
    // An unseen tile is not evidence of a safe refuge, even when old terrain
    // memory resolves the edge and its forecast value happens to be zero.
    {
        Scene s;s.observe();
        std::vector<Tile> local;
        for(const auto& tile:s.queen.get_tiles())
            if(tile.get_position()!=Position(5,4)) local.push_back(tile);
        s.queen.vision=Vision{std::move(local)};
        std::vector<double> forecast(s.memory.cells.size(),1);
        forecast[s.memory.index({5,4})]=0;
        strategy::Simulation initial{s.memory.body,{},true,s.queen.length};
        auto exits=terrain::build(s.queen,s.memory);
        assert(!forage::queen_has_refuge(s.queen,s.memory,initial,forecast,exits));
    }
#endif
    std::cout << "Queen predictive refuge, safe food growth and paid emergency escape checks passed.\n";
}
