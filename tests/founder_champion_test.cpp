#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v100-founder-champion/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int id=2,int initial_units=2) {
        game=&board;ct=&bot;board.round_num=30;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},id,Team::A,Direction::EAST,true};
        bot.length=4;bot.unit_count=initial_units;
        memory.body={{5,5},{4,5},{3,5},{2,5}};
        for(std::size_t i=0;i<memory.body.size();++i)
            bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],id,Team::A,Direction::EAST,i==0};
        memory.observe(bot);
    }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
    void after_first_child(int units=6) {
        auto first=choose();assert(first.action.child_size==2);
        strategy::remember_action(bot,memory,first.action,{},board.round_num);
        assert(memory.splits_done==1);
        // The parent has since regrown from L2 to L4; use its observed body now.
        board.round_num=50;bot.unit_count=units;memory.observe(bot);
    }
    void enemy(int id) {
        bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},id,Team::B,Direction::WEST,true};
        for(auto p:std::vector<Position>{{7,5},{8,5}})
            bot.get_tile(p)->dragon_part=DragonPart{p,id,Team::B,Direction::WEST,false};
        bot.get_tile({8,4})->dragon_part=DragonPart{{8,4},id,Team::B,Direction::SOUTH,false};
        memory.observe(bot);
    }
};

int main() {
    { Scene s;assert(s.memory.reserve_worker);s.after_first_child();
      s.bot.get_tile({6,5})->pearl=true;s.memory.observe(s.bot);auto plan=s.choose();
#ifdef OLD_BASELINE
      assert(plan.action.child_size==2);
#else
      assert(plan.action.child_size==0 && !plan.moves.empty());
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      for(auto d:plan.moves) assert(strategy::simulate_step(s.bot,sim,d,&s.memory));
      assert(sim.length==5); // Retained founder takes growth instead of resetting to L2.
#endif
      s.bot.unit_count=5;plan=s.choose();assert(plan.action.child_size==2);
    }
    { Scene child(4,6);assert(!child.memory.reserve_worker);
      child.memory.splits_done=1;auto plan=child.choose();
      assert(plan.action.child_size==2); // Non-founders keep baseline expansion.
    }
    { Scene founder;founder.bot.unit_count=6;
      auto plan=founder.choose();assert(plan.action.child_size==2);
      assert(founder.memory.reserve_worker && founder.memory.splits_done==0);
    }
    { Scene s;s.after_first_child(10);s.enemy(5);auto plan=s.choose();
#ifdef OLD_BASELINE
      assert(plan.note.find("ATTACK_LARGE_WORKER")!=std::string::npos);
#else
      assert(plan.note.find("ATTACK_LARGE_WORKER")==std::string::npos);
      assert(plan.action.child_size==0);
#endif
    }
    { Scene s;s.after_first_child(10);s.enemy(1);auto plan=s.choose();
      assert(plan.note.find("ATTACK_QUEEN")!=std::string::npos);
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
    { Scene s;s.after_first_child();
      for(auto d:Direction::get_direction_list())
          s.bot.get_tile(s.bot.get_position())->get_edge(d).edge_type=EdgeType::KELP;
      s.memory.observe(s.bot);auto plan=s.choose();
      assert(plan.action.child_size==2 && plan.moves.empty()); // Emergency rescue still works.
    }
#ifdef OLD_BASELINE
    std::cout<<"Baseline founder repeatedly splits L4 and takes ordinary equal trades.\n";
#else
    std::cout<<"Founder expands once, retains growth at six units, rebuilds after collapse, and keeps emergency and Queen attacks.\n";
#endif
}
