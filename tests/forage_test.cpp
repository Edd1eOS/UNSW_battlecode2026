#include "../bot/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64}; Controller bot{2,Team::A,Direction::EAST,Vision{},64}; strategy::Memory memory;
    Scene() {
        game=&board;ct=&bot;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=4;bot.unit_count=4;
        bot.get_tile({5,5})->dragon_part=bot.head;
        memory.body={{5,5},{4,5},{3,5},{2,5}};
        for(int i=1;i<4;++i) bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],2,Team::A,Direction::EAST,false};
        memory.observe_map(bot,30);
    }
};
int main() {
    { Scene s; auto dist=forage::distances(s.bot,s.memory,{9,5},true);
      assert(dist[s.memory.index({8,5})]==1 && dist[s.memory.index({5,5})]==4); }
    { Scene s;s.bot.get_tile({8,5})->dragon_part=DragonPart{{8,5},1,Team::B,Direction::WEST,true};
      auto path=forage::attack_queen(s.bot,s.memory);assert(path.size()==3);
      s.bot.length=2;assert(forage::attack_queen(s.bot,s.memory).empty());
      s.bot.length=4;s.bot.head.dragon_id=0;assert(forage::attack_queen(s.bot,s.memory).empty()); }
    { Scene s;s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},1,Team::B,Direction::WEST,true};
      assert(forage::attack_queen(s.bot,s.memory).size()==1);
      s.bot.unit_count=2;assert(forage::attack_queen(s.bot,s.memory).empty()); }
    { Scene s;s.bot.get_tile({8,5})->dragon_part=DragonPart{{8,5},3,Team::B,Direction::WEST,true};
      auto risk=forage::danger_map(s.bot,s.memory);
      assert(risk[s.memory.index({7,5})]==1 && risk[s.memory.index({6,5})]>0);
      assert(forage::attack_queen(s.bot,s.memory).empty()); }
    { Scene s;s.bot.length=2;s.memory.body={{5,5},{4,5}};
      s.bot.get_tile({3,5})->dragon_part.reset();s.bot.get_tile({2,5})->dragon_part.reset();
      s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},3,Team::B,Direction::WEST,true};
      for(auto p:std::vector<Position>{{7,5},{8,5},{8,6},{7,6}})
          s.bot.get_tile(p)->dragon_part=DragonPart{p,3,Team::B,Direction::WEST,false};
      assert(forage::attack_queen(s.bot,s.memory).empty());
      auto path=forage::attack_queen(s.bot,s.memory,true);
      assert(path.size()==1 && path.front()==Direction(Direction::EAST));
      s.bot.unit_count=2;assert(forage::attack_queen(s.bot,s.memory,true).empty()); }
    { Scene s;
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,42};
      s.memory.observe_map(s.bot,30);
      s.memory.portals[42].push_back({{10,11},false});
      auto& exit=s.memory.cells[s.memory.index({11,11})];
      exit.known=true;exit.pearl=true;exit.seen=30;
      exit.edges[3]=Edge{false,EdgeType::PORTAL,42};
      forage::State state;auto plan=forage::choose(s.bot,s.memory,state);
      assert(plan.moves.size()==1 && plan.moves.front()==Direction(Direction::EAST));
      assert(plan.note.find("PORTAL_SCOUT")!=std::string::npos);
      s.bot.length=7;forage::State long_state;
      assert(forage::choose(s.bot,s.memory,long_state).note.find("PORTAL_SCOUT")==std::string::npos); }
    { Scene s;s.bot.unit_count=64;s.bot.get_tile({6,5})->pearl=true;s.memory.observe_map(s.bot,30);
      forage::State state;auto plan=forage::choose(s.bot,s.memory,state);
      assert(!plan.moves.empty());assert(plan.moves.size()<=1); // L=4 only one free move.
      strategy::Simulation sim{s.memory.body,{},true,s.bot.length};
      for(auto d:plan.moves) assert(strategy::simulate_step(s.bot,sim,d,&s.memory)); }
    std::cout<<"Exploration frontier, Queen attack budget, role guard, threat radius and free move checks passed\n";
}
