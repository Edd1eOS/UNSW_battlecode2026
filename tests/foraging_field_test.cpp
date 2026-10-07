#include "../opponents/generalist-foraging-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{20,20,64};Controller bot{3,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(){game=&board;ct=&bot;bot.head.position={5,5};bot.length=3;bot.unit_count=3;
  std::vector<Tile> tiles;
  for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){tiles.emplace_back(Position{x,y},std::nullopt,-1);
   for(auto d:Direction::get_direction_list())tiles.back().get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::KELP,-1};}
  bot.vision=Vision{std::move(tiles)};memory.body={{5,5},{4,5},{3,5}};}
 void open(Position p,Direction d){const Edge e{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::EMPTY,-1};
  bot.get_tile(p)->get_edge(d)=e;bot.get_tile(p.add_dir(d))->get_edge(d.get_opposite())=e;}
 foraging::Field field(){memory.observe_map(bot,40);return foraging::build(bot,memory);}
};
int main(){
 // One nearby pearl competes with three pearls slightly farther away. The
 // summed discounted field may prefer the productive cluster, using graph
 // distance rather than a straight-line shortcut through walls.
 {Scene s;s.open({5,5},Direction::NORTH);s.open({5,5},Direction::EAST);
  s.open({6,5},Direction::EAST);s.open({7,5},Direction::NORTH);s.open({7,5},Direction::SOUTH);
  for(auto p:std::vector<Position>{{5,4},{7,5},{7,4},{7,6}})s.bot.get_tile(p)->pearl=true;
  auto f=s.field();assert(f.sources.size()==4);
  assert(f.progress(s.memory.index({6,5}),{},20,1)>f.progress(s.memory.index({5,4}),{},20,1));}
 // Food behind a wall is not a source. An unresolved portal is not a guessed
 // route to it; a currently occupied foreign cell cannot seed attraction.
 {Scene s;s.bot.get_tile({6,5})->pearl=true;
  s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,9};
  assert(s.field().sources.empty());
  s.open({5,5},Direction::EAST);s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},9,Team::B,Direction::WEST,false};
  assert(s.field().sources.empty());}
 // Eaten food leaves BOTH endpoint fields, so food income is counted only by
 // the physical movement ledger. A near spawn remains an estimate under .2.
 {Scene s;s.open({5,5},Direction::NORTH);s.bot.get_tile({5,4})->pearl=true;auto f=s.field();
  assert(f.progress(s.memory.index({5,4}),{{5,4}},20,1)==0);
  s.bot.get_tile({5,4})->pearl=false;s.bot.get_tile({5,4})->pearl_time=3;f=s.field();
  assert(f.sources.size()==1&&f.sources.front().weight<=.2);}
 // Portal distance is exactly one observed edge even when its exit is remote.
 {Scene s;s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({7,7})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({8,7})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({8,7})->pearl=true;auto f=s.field();assert(f.sources.size()==1);
  assert(f.sources.front().distance[s.memory.index({5,5})]==1);}
 std::cout<<"Resource field distance/density/ledger scenarios PASS\n";
}
