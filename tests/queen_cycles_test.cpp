#ifdef CURRENT_BOT
#include "../bot/forage.hpp"
#elif defined(OLD_BASELINE)
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v106-queen-cycles/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{25,25,64};
    Controller queen{0,Team::A,Direction::NORTH,Vision{},64};
    strategy::Memory memory;
    Scene(int length=2) {
        game=&board;ct=&queen;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};
        queen.length=length;queen.unit_count=64;
        memory.body={{5,5},{5,6}};
        if(length==3) memory.body.push_back({6,6});
        place_body();observe();
    }
    void place_body() {
        for(auto& tile:queen.vision.tiles) tile.dragon_part.reset();
        queen.get_tile(queen.get_position())->dragon_part=queen.head;
        for(int i=1;i<static_cast<int>(memory.body.size());++i) {
            Direction toward=Direction::NORTH;
            for(auto d:Direction::get_direction_list())
                if(memory.body[i].add_dir(d)==memory.body[i-1]) toward=d;
            if(auto* tile=queen.get_tile(memory.body[i])) tile->dragon_part=
                DragonPart{memory.body[i],queen.get_id(),Team::A,toward,false};
        }
    }
    void observe(int round=100) {memory.observe_map(queen,round);}
    std::vector<Position> square() const {return {{5,5},{6,5},{6,6},{5,6}};}
    forage::State residence() {
        forage::State state;
#ifndef OLD_BASELINE
        state.queen_cycle=square();
#endif
        memory.recent.clear();memory.traffic.assign(memory.cells.size(),0);
        for(int n=0;n<6;++n) for(auto p:square()) memory.recent.push_back(p);
        for(auto p:square()) memory.traffic[memory.index(p)]=20;
        return state;
    }
    void wall(Position p,Direction d) {
        queen.get_tile(p)->get_edge(d)=Edge{false,EdgeType::KELP};
        if(auto* next=queen.get_tile(p.add_dir(d)))
            next->get_edge(d.get_opposite())=Edge{false,EdgeType::KELP};
    }
    void four_cell_room() {
        for(int n=5;n<=6;++n) {
            wall({n,5},Direction::NORTH);wall({n,6},Direction::SOUTH);
            wall({5,n},Direction::WEST);wall({6,n},Direction::EAST);
        }
    }
    void advance(const forage::Plan& plan) {
        assert(plan.moves.size()==1 && plan.action.child_size==0);
        strategy::Simulation next{memory.body,{},true,queen.length};
        assert(strategy::simulate_step(queen,next,plan.moves[0],&memory));
        queen.head.position=next.body.front();queen.head.dir=plan.moves[0];
        queen.length=next.length;memory.body=next.body;
        std::vector<Tile> visible;
        for(int dy=-3;dy<=3;++dy) for(int dx=-3;dx<=3;++dx) {
            Position p{(queen.get_position().x+dx+25)%25,(queen.get_position().y+dy+25)%25};
            const auto* old=queen.get_tile(p);
            if(old) visible.push_back(*old);else visible.emplace_back(p,std::nullopt,-1);
            if(std::find(next.eaten.begin(),next.eaten.end(),p)!=next.eaten.end())
                visible.back().pearl=false;
        }
        queen.vision=Vision{std::move(visible)};place_body();observe(memory.now+1);
        memory.remember(queen.get_position());
    }
};

int main() {
    // After repeated visits to a known square, baseline leaves north toward
    // exploration. A Queen in cycle mode keeps completing the same square.
    {
        Scene s;auto state=s.residence();
        auto plan=forage::choose(s.queen,s.memory,state);
#ifdef OLD_BASELINE
        assert(plan.moves.size()==1 && plan.moves[0]==Direction(Direction::NORTH));
#else
        assert(plan.moves.size()==1 && plan.moves[0]==Direction(Direction::EAST));
        for(auto expected:std::vector<Position>{{6,5},{6,6},{5,6},{5,5},{6,5},{6,6},{5,6},{5,5}}) {
            assert(plan.note.find("QUEEN_CYCLE")!=std::string::npos);
            s.advance(plan);assert(s.queen.get_position()==expected);
            plan=forage::choose(s.queen,s.memory,state);
        }
#endif
    }
    // A second pearl would fill a four-cell loop at length three. Two-lap
    // certification must reject it instead of claiming a permanent refuge.
    {
        Scene s(3);s.four_cell_room();s.queen.get_tile({6,5})->pearl=true;s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")==std::string::npos);
#ifndef OLD_BASELINE
        assert(state.queen_cycle.empty());
        assert(forage::validate_queen_cycle(s.queen,s.memory,s.square()).food<0);
#endif
    }
    // One pearl still leaves a length-two Queen room to keep circling.
    {
        Scene s;s.four_cell_room();s.queen.get_tile({6,5})->pearl=true;s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.moves.size()==1 && plan.moves[0]==Direction(Direction::EAST));
#ifndef OLD_BASELINE
        assert(plan.note.find("QUEEN_CYCLE")!=std::string::npos);
        s.advance(plan);assert(s.queen.length==3);
        plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")!=std::string::npos);
#endif
    }
    // Food on another sustainable loop takes priority over an empty old loop.
    {
        Scene s;s.queen.get_tile({5,4})->pearl=true;s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.moves[0]==Direction(Direction::NORTH));
#ifndef OLD_BASELINE
        assert(plan.note.find("QUEEN_CYCLE")!=std::string::npos);
#endif
    }
    // Every visible enemy head exits cycle mode and returns to normal forage.
    {
        Scene s;s.queen.get_tile({7,7})->dragon_part=
            DragonPart{{7,7},3,Team::B,Direction::NORTH,true};s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")==std::string::npos);
#ifndef OLD_BASELINE
        assert(state.queen_cycle.empty());
#endif
    }
    // New occupancy on the old route also falls back immediately this turn.
    {
        Scene s;s.queen.get_tile({6,5})->dragon_part=
            DragonPart{{6,5},2,Team::A,Direction::SOUTH,false};s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")==std::string::npos);
#ifndef OLD_BASELINE
        assert(state.queen_cycle.empty());
#endif
    }
    // Worker exploration uses the same original policy despite identical visits.
    {
        Scene s;s.queen.head.dragon_id=2;s.place_body();s.observe();
        auto state=s.residence();auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")==std::string::npos);
        assert(plan.moves.size()==1 && plan.moves[0]==Direction(Direction::NORTH));
    }
#ifndef OLD_BASELINE
    // Length eight still fits a ten-cell cycle. Execute one free step rather
    // than accelerating around it, and leave larger Queens on normal forage.
    {
        Scene s;s.queen.length=8;
        s.memory.body={{5,5},{5,6},{5,7},{6,7},{7,7},{8,7},{8,6},{8,5}};
        s.place_body();s.observe();forage::State state;
        state.queen_cycle={{5,5},{6,5},{7,5},{8,5},{8,6},{8,7},{7,7},{6,7},{5,7},{5,6}};
        auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE len=10")!=std::string::npos);
        assert(plan.moves.size()==1 && plan.moves[0]==Direction(Direction::EAST));
        s.queen.length=9;s.memory.body.push_back({7,5});s.place_body();s.observe();
        auto cycle=forage::choose_queen_cycle(s.queen,s.memory,state);
        assert(cycle.food<0 && state.queen_cycle.empty());
    }
    // Cycle discovery does not require an old hint, and occupancy validation
    // rejects a Queen whose complete remembered body is partly unseen today.
    {
        Scene s;s.four_cell_room();s.observe();forage::State state;
        auto plan=forage::choose(s.queen,s.memory,state);
        assert(plan.note.find("QUEEN_CYCLE")!=std::string::npos);
        s.memory.body.back()={5,9};
        auto cycle=forage::choose_queen_cycle(s.queen,s.memory,state);
        assert(cycle.food<0 && state.queen_cycle.empty());
    }
#endif
    std::cout << "Queen stable two-lap cycles, growth limits, live danger/occupancy fallback and worker controls passed.\n";
}
