#include "../opponents/generalist-cooperation-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{20,20,64};Controller bot{3,Team::A,Direction::EAST,Vision{},64};
 strategy::Memory memory;planner::State state;
 Scene() {
  game=&board;ct=&bot;bot.head.position={5,5};bot.length=2;bot.unit_count=4;
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
  bot.vision=Vision{std::move(tiles)};bot.get_tile({5,5})->dragon_part=bot.head;
  bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},3,Team::A,Direction::EAST,false};
  memory.body={{5,5},{4,5}};state.old_length=2;
 }
 void edge(Position p,Direction d,EdgeType kind,int id=-1) {
  auto e=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),kind,id};
  bot.get_tile(p)->get_edge(d)=e;bot.get_tile(p.add_dir(d))->get_edge(d.get_opposite())=e;
 }
 void queen() {
  bot.get_tile({6,4})->dragon_part=DragonPart{{6,4},0,Team::A,Direction::WEST,true};
  bot.get_tile({7,4})->dragon_part=DragonPart{{7,4},0,Team::A,Direction::WEST,false};
  edge({6,4},Direction::NORTH,EdgeType::KELP);edge({6,4},Direction::WEST,EdgeType::KELP);
  memory.observe_map(bot,40);
 }
};
int main() {
 // A tempting food step seals a visible Queen's sole current movement exit.
 // A same-grade alternative keeps it open; no Queen intent is inferred.
 {Scene s;s.queen();s.bot.get_tile({6,5})->pearl=true;s.memory.observe_map(s.bot,40);
  cooperation::Model model(s.bot,s.memory);auto sim=planner::initial(s.bot,s.memory);
  assert(planner::step(s.bot,s.memory,sim,Direction::EAST,false));assert(model.seals_any(sim.body));
  auto baseline_memory=s.memory;auto baseline_state=s.state;auto baseline=planner::choose(s.bot,baseline_memory,baseline_state,false);
  assert(baseline.kind==planner::Kind::Move&&baseline.moves.front()==Direction(Direction::EAST));
  auto plan=planner::choose(s.bot,s.memory,s.state);
#ifndef COOPERATION_DISABLE_EGRESS
  auto actual=planner::initial(s.bot,s.memory);int n=0;for(auto d:plan.moves)assert(planner::step(s.bot,s.memory,actual,d,n++>=1));
  assert(!model.seals_any(actual.body));
#else
  assert(plan.moves==baseline.moves);
#endif
 }
 // An unresolved Queen portal prevents a false claim that all exits close.
 {Scene s;s.queen();s.edge({6,4},Direction::NORTH,EdgeType::PORTAL,99);s.memory.observe_map(s.bot,40);
  cooperation::Model model(s.bot,s.memory);auto sim=planner::initial(s.bot,s.memory);assert(planner::step(s.bot,s.memory,sim,Direction::EAST,false));
  auto evidence=model.exits(model.queens.front(),sim.body);assert(evidence.unknown&&!evidence.seals());}
 // A portal partner currently visible is not penalized as an unseen arrival.
 {Scene s;s.edge({5,5},Direction::NORTH,EdgeType::PORTAL,77);s.edge({6,5},Direction::NORTH,EdgeType::PORTAL,77);
  s.memory.observe_map(s.bot,40);cooperation::Model model(s.bot,s.memory);
  assert(model.arrival_cost({5,5})==0);}
 // A sole unresolved portal is still an escape: arrival risk never hard-vetoes.
 {Scene s;s.bot.head.dragon_id=0;s.bot.get_tile({5,5})->dragon_part=s.bot.head;s.bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},0,Team::A,Direction::EAST,false};
  for(auto d:Direction::get_direction_list())if(d!=Direction(Direction::WEST))s.edge({5,5},d,EdgeType::KELP);
  s.edge({5,5},Direction::NORTH,EdgeType::PORTAL,88);s.memory.observe_map(s.bot,40);
  auto plan=planner::choose(s.bot,s.memory,s.state);assert(plan.kind==planner::Kind::UnknownPortal&&plan.moves.front()==Direction(Direction::NORTH));}
 std::cout<<"Cooperation guards PASS\n";
}
