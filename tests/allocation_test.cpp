#include "../opponents/generalist-allocation-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{20,20,64};Controller bot{3,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(){game=&board;ct=&bot;bot.head.position={5,5};bot.length=3;bot.unit_count=4;
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){tiles.emplace_back(Position{x,y},std::nullopt,-1);
   for(auto d:Direction::get_direction_list())tiles.back().get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::KELP,-1};}
  bot.vision=Vision{std::move(tiles)};memory.body={{5,5},{4,5},{3,5}};
  for(int i=0;i<3;++i)bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],3,Team::A,Direction::EAST,i==0};
  open({3,5},Direction::EAST);open({4,5},Direction::EAST);
 }
 void open(Position p,Direction d){const Edge e{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::EMPTY,-1};
  bot.get_tile(p)->get_edge(d)=e;if(auto* t=bot.get_tile(p.add_dir(d)))t->get_edge(d.get_opposite())=e;}
 void peer(int id,Position head,Position neck,Direction facing){
  open(neck,facing);
  bot.get_tile(head)->dragon_part=DragonPart{head,id,Team::A,facing,true};
  bot.get_tile(neck)->dragon_part=DragonPart{neck,id,Team::A,facing,false};}
 allocation::Result build(){memory.observe_map(bot,40);return allocation::build(bot,memory,[&](int id){return static_cast<int>(planner::observed_chain(bot,memory,id).size());});}
 void conflict(int peer_id=2){open({5,5},Direction::EAST);open({6,5},Direction::EAST);
  open({5,5},Direction::NORTH);open({5,4},Direction::NORTH);
  for(auto p:std::vector<Position>{{6,5},{5,3}})bot.get_tile(p)->pearl=true;
  peer(peer_id,{7,5},{7,6},Direction::NORTH);}
};
int main(){
 {Scene s;s.conflict();auto result=s.build();assert(result.contested&&result.target==s.memory.index({5,3}));
  assert(result.claimed_by_other(s.memory.index({6,5}),s.memory,3));
  planner::State state;auto graph=planner::goals(s.bot,s.memory,state);
#ifndef ALLOCATION_DISABLE
  assert(graph.goal==s.memory.index({5,3}));
#else
  assert(graph.goal==s.memory.index({6,5}));
#endif
  assert(graph.food_sites==2); // Allocation cannot change expansion's resource count.
  auto sim=planner::initial(s.bot,s.memory);assert(planner::step(s.bot,s.memory,sim,Direction::EAST,false));
  assert(sim.length==4&&sim.eaten.size()==1); // Another claim never deducts actual food.
  auto plan=planner::choose(s.bot,s.memory,state);assert(plan.kind==planner::Kind::Move);
  auto executed=planner::initial(s.bot,s.memory);int step_count=0;
  for(auto d:plan.moves)assert(planner::step(s.bot,s.memory,executed,d,step_count++>=1));
  assert(plan.food==static_cast<int>(executed.eaten.size())&&plan.paid==std::max(0,step_count-1));
  std::cout<<"Conflicting visible agents get distinct targets; actual claimed pearl still grows body\n";
 }
 {Scene s;s.open({5,5},Direction::NORTH);s.bot.get_tile({5,4})->pearl=true;auto result=s.build();assert(!result.contested);
  planner::State state;state.goal=s.memory.index({5,4});state.goal_since=40;
  auto graph=planner::goals(s.bot,s.memory,state);
  assert(graph.goal==s.memory.index({5,4})&&graph.field[s.memory.index({5,5})]==1);
  std::cout<<"Single-agent precise old-goal fallback\n";
 }
 {Scene s;s.bot.get_tile({6,5})->pearl=true;s.peer(2,{7,5},{7,6},Direction::NORTH);
  s.open({7,5},Direction::WEST);auto result=s.build();assert(!result.contested&&result.target<0);
  // The acting dragon has a wall, even though its peer has a legal route.
  std::cout<<"Walls do not create imaginary self reachability\n";
 }
 {Scene s;s.bot.get_tile({8,7})->pearl=true;s.peer(4,{8,8},{7,8},Direction::EAST);s.open({8,8},Direction::NORTH);
  s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  auto unknown=s.build();assert(!unknown.contested);
  assert(unknown.unknown);
  s.bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({7,7})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  s.bot.get_tile({8,7})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
  auto known=s.build();assert(known.contested&&known.target==s.memory.index({8,7})&&known.self_eta==1);
  std::cout<<"Unresolved portal excluded; parsed directed landing is one step\n";
 }
 {Scene s;s.conflict(0);auto result=s.build();assert(result.claimed_by_other(s.memory.index({6,5}),s.memory,3));
  int claimed=0;for(int id:result.owner)claimed+=id==0;assert(claimed==1);
  assert(result.target==s.memory.index({5,3}));std::cout<<"Queen timely priority is capped at one real pearl\n";
 }
 {Scene s;s.open({5,5},Direction::EAST);s.bot.get_tile({6,5})->pearl=true;
  s.peer(0,{8,8},{7,8},Direction::EAST);
  s.open({8,8},Direction::NORTH);s.open({8,7},Direction::NORTH);s.open({8,6},Direction::NORTH);
  s.open({8,5},Direction::WEST);s.open({7,5},Direction::WEST);
  auto result=s.build();assert(result.contested&&result.target==s.memory.index({6,5}));
  assert(result.owner.front()==3);std::cout<<"Remote slow Queen cannot reserve the worker's imminent food\n";
 }
 {Scene s;s.conflict();s.build();
  auto lower=planner::observed_chain(s.bot,s.memory,2).size();assert(lower==2);
  auto result=s.build();assert(result.agents[1].length_lower_bound==2&&!result.agents[1].own);
  std::cout<<"Peer length is current observed chain lower bound, not global full length\n";
 }
}
