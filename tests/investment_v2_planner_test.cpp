#include "../opponents/generalist-investment-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(){game=&board;ct=&bot;bot.head.position={5,5};bot.length=6;bot.unit_count=10;
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
  bot.vision=Vision{std::move(tiles)};memory.body={{5,5},{4,5},{3,5},{3,6},{4,6},{5,6}};
  std::vector<Direction> dirs={Direction::EAST,Direction::EAST,Direction::EAST,Direction::NORTH,Direction::WEST,Direction::WEST};
  for(int i=0;i<6;++i)bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],2,Team::A,dirs[i],i==0};
 }
 void wall(Position p,Direction d){bot.get_tile(p)->get_edge(d)=Edge{false,EdgeType::KELP,-1};Position q=p.add_dir(d);
  if(auto* t=bot.get_tile(q))t->get_edge(d.get_opposite())=Edge{false,EdgeType::KELP,-1};}
 void observed(){memory.observe_map(bot,30);}
};
int main(){
 {planner::Candidate split,food_move,cover_move;
  split.kind=planner::Kind::Split;split.future.depth=6;
  food_move.future.depth=6;cover_move.future.depth=6;
  for(auto* p:{&split,&food_move,&cover_move}){p->joint=investment::Forecast{};p->joint->complete=true;}
  split.joint->food=2;split.joint->exploration=2;
  food_move.joint->food=3;food_move.joint->exploration=1;
  cover_move.joint->food=1;cover_move.joint->exploration=3;
  assert(!planner::investment_dominated(split,food_move,false,6));
  assert(!planner::investment_dominated(split,cover_move,false,6));
  food_move.joint->exploration=3;food_move.future.depth=2;
  assert(!planner::investment_dominated(split,food_move,false,6)); // Known finite food bait cannot veto full continuation.
  food_move.future.depth=6;assert(planner::investment_dominated(split,food_move,false,6));
  food_move.imminent=true;assert(!planner::investment_dominated(split,food_move,true,6));
  std::cout<<"Same-path Pareto dominance after safety: no synthetic maxima or dead-end food veto\n";
 }
 {Scene s;s.wall({5,5},Direction::EAST);
  for(auto p:std::vector<Position>{{6,6},{7,6},{8,6}})s.bot.get_tile(p)->pearl=true;
  s.observed();planner::State state;auto p=planner::choose(s.bot,s.memory,state);std::cout<<p.note<<"\n";
#ifdef INVESTMENT_DISABLE_JOINT
  assert(p.kind!=planner::Kind::Split);
#else
  assert(p.kind==planner::Kind::Split&&p.action.child_size==2);
  assert(p.food==0&&p.paid==0); // The split itself creates no income.
#endif
 }
#ifndef INVESTMENT_DISABLE_JOINT
 {Scene s;s.wall({5,5},Direction::EAST);
  for(auto p:std::vector<Position>{{6,6},{7,6},{8,6}})s.bot.get_tile(p)->pearl=true;
  s.observed();s.memory.reserve_worker=true;s.memory.splits_done=1;
  planner::State state;auto p=planner::choose(s.bot,s.memory,state);
  assert(state.reserve&&p.kind!=planner::Kind::Split);
  assert(p.note.find("investment_reject_capital=1")!=std::string::npos);
  std::cout<<"Founder ordinary investment has positive family net but loses max capital: rejected, MOVE retained\n";
 }
#endif
 {Scene s; // No current food and no unseen terrain boundary: a sealed empty room.
  for(int x=2;x<=8;++x){s.wall({x,2},Direction::NORTH);s.wall({x,8},Direction::SOUTH);}
  for(int y=2;y<=8;++y){s.wall({2,y},Direction::WEST);s.wall({8,y},Direction::EAST);}
  s.observed();planner::State state;auto p=planner::choose(s.bot,s.memory,state);
  assert(p.kind!=planner::Kind::Split);std::cout<<"Closed dry region: no ordinary investment\n";
 }
 {Scene s;s.bot.length=8;s.bot.unit_count=10;
  s.bot.get_tile({8,8})->dragon_part=DragonPart{{8,8},4,Team::A,Direction::NORTH,true};
  regional_role::State role;bool r=regional_role::update(s.bot,s.memory,role,[](int){return 9;});
  assert(!r&&role.visible_winner==4);
  s.bot.get_tile({8,8})->dragon_part.reset();r=regional_role::update(s.bot,s.memory,role,[](int){return 9;});
  assert(r&&role.champion); // Unseen opponents are not global length evidence.
  s.bot.length=7;s.bot.unit_count=2;r=regional_role::update(s.bot,s.memory,role,[](int){return 0;});assert(r);
  s.bot.get_tile({8,8})->dragon_part=DragonPart{{8,8},4,Team::A,Direction::NORTH,true};
  r=regional_role::update(s.bot,s.memory,role,[](int){return 9;});assert(!r);
  s.memory.reserve_worker=true;s.memory.splits_done=1;
  r=regional_role::update(s.bot,s.memory,role,[](int){return 9;});assert(r&&role.founder);
  std::cout<<"Regional visible competitor retires natural role; founder persists\n";
 }
 {Scene s;s.bot.length=8;s.memory.body.push_back({5,7});s.memory.body.push_back({4,7});
  s.bot.get_tile({5,7})->dragon_part=DragonPart{{5,7},2,Team::A,Direction::NORTH,false};
  s.bot.get_tile({4,7})->dragon_part=DragonPart{{4,7},2,Team::A,Direction::EAST,false};
  const std::vector<Position> body={{8,8},{8,7},{7,7},{6,7},{6,8},{5,8},{4,8},{3,8},{2,8}};
  const std::vector<Direction> dirs={Direction::SOUTH,Direction::SOUTH,Direction::EAST,Direction::EAST,
    Direction::NORTH,Direction::EAST,Direction::EAST,Direction::EAST,Direction::EAST};
  for(int i=0;i<9;++i)s.bot.get_tile(body[i])->dragon_part=DragonPart{body[i],4,Team::A,dirs[i],i==0};
  s.observed();planner::State state;state.reserve=true;state.region.champion=true;
  assert(planner::observed_chain(s.bot,s.memory,4).size()==9);
  planner::update_role(s.bot,s.memory,state);
#ifdef INVESTMENT_KEEP_V5_ROLES
  assert(state.reserve);
#else
  assert(!state.reserve&&state.region.visible_winner==4);
#endif
  std::cout<<"Current nine-segment visible chain proves regional retirement; no global length assumed\n";
 }
 {Scene s;s.observed();investment::Context context(s.bot,s.memory);
  auto original=planner::initial(s.bot,s.memory);
  auto f=investment::evaluate_split(s.bot,s.memory,original,2,context,320);
  assert(f.valid&&f.complete&&f.world.records.size()==3);
  assert(f.world.actors[0].length+f.world.actors[1].length==s.bot.length+f.food-f.paid);
  assert(f.world.records[0].actor==1&&f.world.records[1].actor==0&&f.world.records[2].actor==1);
  auto moved=original;assert(planner::step(s.bot,s.memory,moved,Direction::NORTH,false));
  auto g=investment::evaluate_move(s.bot,s.memory,moved,{Direction::NORTH},0,context,96);
  assert(g.complete&&g.world.records.size()==1&&g.world.records[0].actor==0);
  assert(f.food==0&&f.paid==0&&g.food==0&&g.paid==0);
  std::cout<<"Same two-round schedule, split has birth action then parent-child; move has next parent only\n";
 }
}
