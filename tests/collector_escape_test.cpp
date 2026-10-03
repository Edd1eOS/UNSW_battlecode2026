#ifdef OLD_BASELINE
#include "../opponents/v99-queen-refuge/forage.hpp"
#else
#include "../opponents/v108-collector-escape/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int id=2) {
        game=&board;ct=&bot;board.round_num=100;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},id,Team::A,Direction::EAST,true};
        bot.length=8;bot.unit_count=8;
        memory.body={{5,5},{4,5},{3,5},{2,5},{2,4},{2,3},{3,3},{3,4}};
        place(memory.body,id,Team::A);
        place({{5,3},{6,3},{7,3}},3,Team::B);
        place({{7,5},{7,4},{6,4}},5,Team::B);
        place({{5,7},{6,7},{6,6}},7,Team::B);
        memory.observe(bot);
    }
    void place(const std::deque<Position>& body,int id,Team team) {
        for(std::size_t i=0;i<body.size();++i) {
            Direction toward_head=Direction::EAST;
            if(i) for(auto d:Direction::get_direction_list())
                if(body[i].add_dir(d)==body[i-1]) toward_head=d;
            bot.get_tile(body[i])->dragon_part=DragonPart{body[i],id,team,toward_head,i==0};
        }
    }
    strategy::Simulation finish(const forage::Plan& plan) {
        strategy::Simulation sim{memory.body,{},true,bot.length};
        const int free_steps=(bot.length+3)/4;
        for(int i=0;i<static_cast<int>(plan.moves.size());++i) {
            assert(strategy::simulate_step(bot,sim,plan.moves[i],&memory));
            if(i>=free_steps) {--sim.length;if(static_cast<int>(sim.body.size())>sim.length) sim.body.pop_back();}
        }
        return sim;
    }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
    void wall(Direction d) {
        bot.get_tile(bot.get_position())->get_edge(d).edge_type=EdgeType::KELP;
        bot.get_tile(bot.get_position().add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;
    }
};

int main() {
    { Scene s;for(const auto p:std::vector<Position>{{5,3},{7,5},{5,7}})
          assert(forage::enemy_reach(s.bot,s.memory,*s.bot.get_tile(p))==2);
      auto plan=s.choose();assert(s.state.collector && plan.action.child_size==0);
      auto sim=s.finish(plan);const auto danger=forage::danger_map(s.bot,s.memory);
      assert(sim.eaten.empty()); // No food is required to justify the paid survival route.
#ifdef OLD_BASELINE
      assert(plan.moves.size()<=2 && sim.length==8);
      assert(danger[s.memory.index(sim.body.front())]>0);
#else
      assert(plan.moves.size()==3 && sim.length==7);
      assert(danger[s.memory.index(sim.body.front())]==0);
      int budget=110;assert(strategy::search_survival(s.bot,sim,0,6,budget,&s.memory).depth==6);
      assert(plan.note.find("paid_escape=1")!=std::string::npos);
      strategy::remember_action(s.bot,s.memory,plan.action,plan.moves,100);
      assert(s.memory.body==sim.body && s.memory.body.size()==7);
#endif
    }
    { Scene s;for(auto p:std::vector<Position>{{5,7},{6,7},{6,6}}) s.bot.get_tile(p)->dragon_part.reset();
      s.memory.observe(s.bot);auto plan=s.choose();
      assert(plan.action.child_size==0 && plan.moves.size()<=2);
      assert(s.finish(plan).length==8 && plan.note.find("paid_escape=")==std::string::npos);
    }
    { Scene s;s.place({{5,7},{6,7},{6,6},{7,6}},7,Team::B);
      s.wall(Direction::NORTH);s.wall(Direction::EAST);s.memory.observe(s.bot);
      auto plan=s.choose();assert(plan.action.child_size==0);auto sim=s.finish(plan);
      const auto danger=forage::danger_map(s.bot,s.memory);
#ifdef OLD_BASELINE
      assert(plan.moves.size()<=2 && danger[s.memory.index(sim.body.front())]>0);
#else
      assert(plan.moves.size()==4 && sim.length==6 && sim.eaten.empty());
      assert(danger[s.memory.index(sim.body.front())]==0 && plan.note.find("paid_escape=2")!=std::string::npos);
      strategy::remember_action(s.bot,s.memory,plan.action,plan.moves,100);
      assert(s.memory.body==sim.body && s.memory.body.size()==6);
#endif
    }
    { Scene s(4);s.bot.unit_count=96;auto plan=s.choose();
      assert(!s.state.collector && plan.action.child_size==0 && plan.moves.size()<=2);
      assert(s.finish(plan).length==8 && plan.note.find("paid_escape=")==std::string::npos);
    }
    { Scene s(0);auto plan=s.choose();
      assert(plan.action.child_size==0 && !plan.moves.empty());
      assert(plan.note.find("paid_escape=")==std::string::npos); // Queen keeps its original paid planner.
    }
#ifdef OLD_BASELINE
    std::cout<<"Baseline grown collector keeps a free endpoint inside visible enemy sprint reach.\n";
#else
    std::cout<<"Collector buys one zero-food escape step, keeps six continuation steps, accounts for body cost, and preserves free-safe/other roles.\n";
#endif
}
