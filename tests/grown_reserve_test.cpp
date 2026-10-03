#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v101-grown-reserve/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{4,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int length=10,int units=8) {
        game=&board;ct=&bot;board.round_num=100;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},4,Team::A,Direction::EAST,true};
        bot.length=length;bot.unit_count=units;
        memory.body={{5,5},{4,5},{3,5},{2,5},{2,4},{2,3},{3,3},{4,3},{5,3},{6,3}};
        while(static_cast<int>(memory.body.size())>length) memory.body.pop_back();
        for(std::size_t i=0;i<memory.body.size();++i) {
            Direction toward_head=Direction::EAST;
            if(i) for(auto d:Direction::get_direction_list())
                if(memory.body[i].add_dir(d)==memory.body[i-1]) toward_head=d;
            bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],4,Team::A,toward_head,i==0};
        }
        memory.observe(bot);
    }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
};

int main() {
    { Scene s;s.bot.get_tile({6,5})->pearl=true;s.memory.observe(s.bot);auto plan=s.choose();
      assert(!s.state.collector);
#ifdef OLD_BASELINE
      assert(plan.action.child_size==5);
#else
      assert(plan.action.child_size==0 && !plan.moves.empty());
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      for(auto d:plan.moves) assert(strategy::simulate_step(s.bot,sim,d,&s.memory));
      assert(sim.length==11); // The grown worker takes the pearl with its length intact.
#endif
      s.bot.unit_count=7;plan=s.choose();assert(plan.action.child_size==5);
    }
    { Scene s(9,8);auto plan=s.choose();
      assert(!s.state.collector && plan.action.child_size==4);
    }
    { Scene s;s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},1,Team::B,Direction::WEST,true};
      s.memory.observe(s.bot);auto plan=s.choose();
      assert(plan.action.child_size==0 && plan.note.find("ATTACK_QUEEN")!=std::string::npos);
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
    { Scene s;for(auto d:Direction::get_direction_list())
          s.bot.get_tile(s.bot.get_position())->get_edge(d).edge_type=EdgeType::KELP;
      s.memory.observe(s.bot);auto plan=s.choose();
      assert(plan.action.child_size==8 && plan.moves.empty()); // Emergency rescue still works.
    }
#ifdef OLD_BASELINE
    std::cout<<"Baseline ordinary worker divides L10 into two L5 units.\n";
#else
    std::cout<<"Grown reserve retains L10, L9 still divides, seven units rebuild, and Queen attacks and emergency rescue remain.\n";
#endif
}
