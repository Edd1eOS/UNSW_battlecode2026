#ifdef OLD_BASELINE
#include "../opponents/v103-queen-threat-priority/forage.hpp"
#else
#include "../opponents/v107-queen-sprint-priority/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{17,17,64};
    Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int id=0) {
        game=&board;ct=&bot;board.round_num=100;
        std::vector<Tile> tiles;
        for(int y=7;y<=13;++y) for(int x=7;x<=13;++x) {
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
            for(auto d:Direction::get_direction_list()) tiles.back().get_edge(d).edge_type=EdgeType::KELP;
        }
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{10,10},id,Team::A,Direction::EAST,true};
        bot.length=2;bot.unit_count=2;memory.body={{10,10},{10,11}};
        bot.get_tile({10,10})->dragon_part=bot.head;
        bot.get_tile({10,11})->dragon_part=DragonPart{{10,11},id,Team::A,Direction::NORTH,false};
        open({10,10},Direction::SOUTH);
        // Terrain is a cycle, so the terminal-branch filter permits it. The
        // occupied cell at (10,9) cuts the visible walking route after 7 steps.
        const std::vector<Position> cycle{{10,10},{9,10},{8,10},{7,10},{7,9},{7,8},{8,8},{9,8},{10,8},{10,9}};
        for(std::size_t i=0;i<cycle.size();++i) {
            auto from=cycle[i],to=cycle[(i+1)%cycle.size()];
            for(auto d:Direction::get_direction_list()) if(from.add_dir(d)==to) open(from,d);
        }
        // This visible enemy tail points through a portal to an unseen body,
        // so it can seal the cycle without inventing an adjacent enemy head.
        bot.get_tile({10,9})->dragon_part=DragonPart{{10,9},5,Team::B,Direction::WEST,false};
        bot.get_tile({10,9})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,99};
        bot.get_tile({9,9})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,99};
        // The east endpoint is immediately reachable by a length-two enemy.
        open({10,10},Direction::EAST);open({11,10},Direction::EAST);open({12,10},Direction::EAST);
        bot.get_tile({12,10})->dragon_part=DragonPart{{12,10},3,Team::B,Direction::WEST,true};
        bot.get_tile({13,10})->dragon_part=DragonPart{{13,10},3,Team::B,Direction::WEST,false};
        // Its north branch ends just outside the real 7x7 vision. This yields
        // uncertainty, which outranks the 7-step known route in the baseline.
        for(int y=10;y>=7;--y) open({11,y},Direction::NORTH);
        memory.observe(bot);
    }
    void open(Position p,Direction d) {
        bot.get_tile(p)->get_edge(d).edge_type=EdgeType::EMPTY;
        if(auto* other=bot.get_tile(p.add_dir(d))) other->get_edge(d.get_opposite()).edge_type=EdgeType::EMPTY;
    }
    void close(Position p,Direction d) {
        bot.get_tile(p)->get_edge(d).edge_type=EdgeType::KELP;
        if(auto* other=bot.get_tile(p.add_dir(d))) other->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;
        memory.observe(bot);
    }
    void sprint_enemy() {
        bot.get_tile({12,10})->dragon_part.reset();
        bot.get_tile({13,10})->dragon_part=DragonPart{{13,10},3,Team::B,Direction::WEST,true};
        bot.get_tile({13,9})->dragon_part=DragonPart{{13,9},3,Team::B,Direction::SOUTH,false};
        bot.get_tile({12,9})->dragon_part=DragonPart{{12,9},3,Team::B,Direction::EAST,false};
        open({13,9},Direction::SOUTH);open({12,9},Direction::EAST);
        memory.observe(bot);
    }
    strategy::Lookahead future(Direction d) {
        strategy::Simulation sim{memory.body,{},true,bot.length};
        assert(strategy::simulate_step(bot,sim,d,&memory));
        int budget=220;return strategy::search_survival(bot,sim,0,8,budget,&memory);
    }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
};

int main() {
    { Scene s;auto safe=s.future(Direction::WEST),unsafe=s.future(Direction::EAST);
      assert(safe.depth==7 && !safe.uncertain);
      assert(unsafe.depth>=2 && unsafe.uncertain);
      const auto danger=forage::danger_map(s.bot,s.memory);
      assert(danger[s.memory.index({9,10})]==0);
      assert(danger[s.memory.index({11,10})]>=1);
      const auto exits=terrain::build(s.bot,s.memory);
      assert(!exits.worsens(s.memory,{10,10},{9,10}));
      auto plan=s.choose();assert(plan.action.child_size==0 && plan.moves.size()==1);
      assert(plan.moves.front()==Direction(Direction::WEST));
    }
    { Scene s;s.sprint_enemy();auto safe=s.future(Direction::WEST),unsafe=s.future(Direction::EAST);
      assert(forage::enemy_reach(s.bot,s.memory,*s.bot.get_tile({13,10}))==2);
      assert(safe.depth==7 && !safe.uncertain && unsafe.uncertain);
      const auto danger=forage::danger_map(s.bot,s.memory);
      assert(danger[s.memory.index({11,10})]==0.25);
      assert(danger[s.memory.index({9,10})]==0);
      auto plan=s.choose();assert(plan.action.child_size==0 && plan.moves.size()==1);
#ifdef OLD_BASELINE
      assert(plan.moves.front()==Direction(Direction::EAST));
#else
      assert(plan.moves.front()==Direction(Direction::WEST));
#endif
    }
    { Scene s;s.close({10,10},Direction::WEST);auto plan=s.choose();
      assert(plan.action.child_size==0 && plan.moves.size()==1);
      assert(plan.moves.front()==Direction(Direction::EAST)); // All unsafe still permits escape.
    }
    { Scene worker(4);auto plan=worker.choose();
      assert(plan.action.child_size==0 && plan.moves.size()==1);
      assert(plan.moves.front()==Direction(Direction::WEST)); // Workers retain baseline ranking.
    }
#ifdef OLD_BASELINE
    std::cout<<"v103 avoids direct attack but selects a two-step sprint endpoint over seven known safe steps.\n";
#else
    std::cout<<"Queen avoids visible sprint reach; direct threat, all-unsafe escape and worker ranking checks pass.\n";
#endif
}
