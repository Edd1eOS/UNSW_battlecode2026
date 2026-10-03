#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v98-longest-harvest/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{4,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int length=4,int units=24,int id=4) {
        game=&board;ct=&bot;board.round_num=120;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},id,Team::A,Direction::EAST,true};
        bot.length=length;bot.unit_count=units;
        const std::deque<Position> body{{5,5},{4,5},{3,5},{2,5},{2,4},{2,3},{3,3},{4,3}};
        memory.body=body;
        while(static_cast<int>(memory.body.size())>length) memory.body.pop_back();
        for(std::size_t i=0;i<memory.body.size();++i) {
            Direction toward_head=Direction::EAST;
            if(i) for(auto d:Direction::get_direction_list())
                if(memory.body[i].add_dir(d)==memory.body[i-1]) toward_head=d;
            bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],id,Team::A,toward_head,i==0};
        }
        observe();
    }
    void observe() { memory.observe_map(bot,board.round_num); }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
    void enemy(Position head,int id=5,int length=4) {
        bot.get_tile(head)->dragon_part=DragonPart{head,id,Team::B,Direction::WEST,true};
        for(int i=1;i<length;++i) {
            Position p{head.x+i,head.y};
            if(auto* tile=bot.get_tile(p)) tile->dragon_part=DragonPart{p,id,Team::B,Direction::WEST,false};
        }
        observe();
    }
};

int main() {
    { Scene s;auto plan=s.choose();
#ifdef OLD_BASELINE
      assert(plan.action.child_size==2);
#else
      assert(plan.action.child_size==0 && !s.state.collector);
#endif
      s.bot.unit_count=5;plan=s.choose();
      assert(plan.action.child_size==2); // Expansion is still fast after a population collapse.
    }
    { Scene s(8,24);auto plan=s.choose();
#ifdef OLD_BASELINE
      assert(!s.state.collector && plan.action.child_size==4);
#else
      assert(s.state.collector && plan.action.child_size==0);
      assert(plan.note.find("RESERVE")!=std::string::npos);
      assert(!plan.moves.empty() && plan.moves.size()<=2); // Only free moves are available.
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      for(auto d:plan.moves) assert(strategy::simulate_step(s.bot,sim,d,&s.memory));
      s.bot.unit_count=5;plan=s.choose();
      assert(s.state.collector && plan.action.child_size==4); // Sticky reserve can rebuild the colony.
#endif
    }
    { Scene s(4,24,2);s.enemy({6,5},5,3);
      s.bot.get_tile({8,4})->dragon_part=DragonPart{{8,4},5,Team::B,Direction::SOUTH,false};
      s.observe();auto plan=s.choose();
      assert(s.state.collector);
#ifdef OLD_BASELINE
      assert(plan.note.find("ATTACK_LARGE_WORKER")!=std::string::npos);
#else
      assert(plan.note.find("ATTACK_LARGE_WORKER")==std::string::npos);
      assert(plan.action.child_size==0);
      // Queen elimination remains the first scoring priority, including paid attacks.
      s.bot.get_tile({6,5})->dragon_part.reset();
      s.bot.get_tile({7,5})->dragon_part.reset();
      s.enemy({8,5},1,1);plan=s.choose();
      assert(plan.note.find("ATTACK_QUEEN")!=std::string::npos && plan.moves.size()==3);
      assert(plan.moves.size()>static_cast<std::size_t>((s.bot.length+3)/4));
#endif
    }
    { Scene s(8,24,2);s.enemy({8,5},5,1);
      s.bot.get_tile({6,5})->pearl=true;s.observe();auto plan=s.choose();
      assert(s.state.collector && plan.action.child_size==0);
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      for(auto d:plan.moves) assert(strategy::simulate_step(s.bot,sim,d,&s.memory));
      const auto danger=forage::queen_danger(s.bot,s.memory);
#ifdef OLD_BASELINE
      assert(danger[s.memory.index(sim.body.front())]>0);
#else
      assert(danger[s.memory.index(sim.body.front())]==0);
#endif
    }
#ifdef OLD_BASELINE
    std::cout<<"Baseline splits saturated workers and trades established collectors for ordinary enemies.\n";
#else
    std::cout<<"Harvest reserve retains earned stride, avoids ordinary trades and reachable heads, rebuilds after collapse, and still attacks Queen.\n";
#endif
}
