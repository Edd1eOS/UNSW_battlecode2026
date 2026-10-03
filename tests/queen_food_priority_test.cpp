#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v105-queen-food-priority/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{4,Team::A,Direction::NORTH,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int length=3,int units=6) {
        game=&board;ct=&bot;board.round_num=30;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},4,Team::A,Direction::NORTH,true};
        bot.length=length;bot.unit_count=units;
        memory.body=length==3?std::deque<Position>{{5,5},{5,6},{5,7}}
                             :std::deque<Position>{{5,5},{4,5},{3,5},{2,5}};
        body();
    }
    void body() {
        for(std::size_t i=0;i<memory.body.size();++i) {
            Direction toward_head=bot.get_dir();
            if(i) for(auto d:Direction::get_direction_list())
                if(memory.body[i].add_dir(d)==memory.body[i-1]) toward_head=d;
            bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],bot.get_id(),Team::A,toward_head,i==0};
        }
    }
    void queen(Position p) {
        bot.get_tile(p)->dragon_part=DragonPart{p,0,Team::A,Direction::NORTH,true};
        const auto tail=p.add_dir(Direction::SOUTH);
        bot.get_tile(tail)->dragon_part=DragonPart{tail,0,Team::A,Direction::NORTH,false};
    }
    void observe() { memory.observe(bot); }
    forage::Plan choose() { observe();return forage::choose(bot,memory,state); }
    void foods() {
        queen({8,5});bot.get_tile({6,5})->pearl=true;bot.get_tile({2,5})->pearl=true;
    }
    void wall(Direction d) {
        bot.get_tile(bot.get_position())->get_edge(d).edge_type=EdgeType::KELP;
        bot.get_tile(bot.get_position().add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;
    }
};

int main() {
    { Scene s;s.foods();auto plan=s.choose();assert(plan.action.child_size==0 && plan.moves.size()==1);
#ifdef OLD_BASELINE
      assert(plan.moves.front()==Direction(Direction::EAST));
#else
      assert(plan.moves.front()==Direction(Direction::WEST));
      assert(forage::position(s.memory,s.state.goal)==Position(2,5));
#endif
    }
    { Scene s(3,5);s.foods();auto plan=s.choose();
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
    { Scene s;s.bot.head.dragon_id=0;s.body();
      s.bot.get_tile({6,5})->pearl=true;s.bot.get_tile({2,5})->pearl=true;auto plan=s.choose();
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
    { Scene s;s.queen({8,5});s.bot.get_tile({6,5})->pearl=true;
      s.wall(Direction::NORTH);s.wall(Direction::WEST);auto plan=s.choose();
      assert(plan.action.child_size==0 && plan.moves.size()==1);
      assert(plan.moves.front()==Direction(Direction::EAST)); // The only escape can eat reserved food.
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      assert(strategy::simulate_step(s.bot,sim,plan.moves.front(),&s.memory) && sim.length==4);
    }
    { Scene s(4);s.queen({6,5});auto plan=s.choose();
#ifdef OLD_BASELINE
      assert(plan.action.child_size==2);
#else
      assert(plan.action.child_size==0 && !plan.moves.empty());
#endif
      for(auto d:Direction::get_direction_list()) s.wall(d);
      plan=s.choose();assert(plan.action.child_size==2 && plan.moves.empty()); // Rescue is still permitted near Queen.
    }
    { Scene s(4);s.queen({7,5});auto plan=s.choose();
      assert(plan.action.child_size==2); // Tail is five cells from Queen.
    }
    { Scene s;s.queen({8,5});
      s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},1,Team::B,Direction::WEST,true};
      s.bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},1,Team::B,Direction::WEST,false};
      auto plan=s.choose();assert(plan.note.find("ATTACK_QUEEN")!=std::string::npos);
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
    { Scene s;s.bot.get_tile({6,5})->pearl=true;s.bot.get_tile({2,5})->pearl=true;
      auto plan=s.choose();assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
    }
#ifdef OLD_BASELINE
    std::cout<<"Baseline worker takes nearby Queen food and splits a tail four cells from Queen.\n";
#else
    std::cout<<"Visible Queen gets local food priority; small colonies, Queen growth, escape, distant splits and attacks remain available.\n";
#endif
}
