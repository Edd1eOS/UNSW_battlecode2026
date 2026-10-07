#include "../opponents/generalist-investment-v2/investment.hpp"
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
  memory.observe_map(bot,30);}
 investment::World split(){investment::World w;assert(investment::split_world(bot,memory,{memory.body,{},true,6},2,w));return w;}
};
int main(){
 {Scene s;auto w=s.split();assert(w.count==2&&w.actors[0].body.front()==Position(5,5));
  assert(w.actors[0].length==4&&w.actors[1].length==2&&w.actors[1].body.front()==Position(5,6));
  assert(w.actors[1].body[1]==Position(4,6)&&w.actors[1].facing==Direction(Direction::EAST));
  assert(investment::step(s.bot,s.memory,w,1,Direction::NORTH,false)==investment::Step::Blocked);
  assert(investment::step(s.bot,s.memory,w,1,Direction::WEST,false)==investment::Step::Blocked);
  assert(w.food==0&&w.paid==0&&w.actors[0].length+w.actors[1].length==6);}
 {Scene s;auto w=s.split();s.bot.get_tile({6,6})->pearl=true;s.bot.get_tile({7,6})->pearl=true;
  assert(investment::step(s.bot,s.memory,w,1,Direction::EAST,true)==investment::Step::Unaffordable);
  assert(w.food==0&&w.paid==0);
  assert(investment::apply_action(s.bot,s.memory,w,1,{Direction::EAST,Direction::EAST}));
  assert(w.food==2&&w.paid==1&&w.actors[1].length==3);
  assert(w.records.back().free_steps==1&&w.records.back().start_length==2);
  assert(w.actors[0].length+w.actors[1].length==6+w.food-w.paid);}
 {Scene s;auto w=s.split();s.bot.get_tile({6,6})->pearl=true;
  assert(investment::step(s.bot,s.memory,w,1,Direction::EAST,false)==investment::Step::Legal);
  assert(investment::step(s.bot,s.memory,w,0,Direction::EAST,false)==investment::Step::Legal);
  assert(investment::step(s.bot,s.memory,w,0,Direction::SOUTH,true)==investment::Step::Blocked);
  assert(w.food==1&&w.paid==0); // Payment does not release the child's old tail.
  for(auto d:std::vector<Direction>{Direction::EAST,Direction::EAST,Direction::SOUTH})
   assert(investment::step(s.bot,s.memory,w,1,d,false)==investment::Step::Legal);
  assert(investment::step(s.bot,s.memory,w,0,Direction::SOUTH,false)==investment::Step::Legal);
  assert(w.food==1&&w.actors[0].length==4); // Same pearl cannot be counted twice.
 }
 {Scene s;auto w=s.split();s.bot.get_tile({6,6})->dragon_part=DragonPart{{6,6},9,Team::B,Direction::SOUTH,false};
  assert(investment::step(s.bot,s.memory,w,1,Direction::EAST,false)==investment::Step::Blocked);}
 {Scene s;auto w=s.split();w.actors[1].body={{8,5},{7,5}};w.actors[1].length=2;
  const auto old=w.actors[1].body;
  assert(investment::step(s.bot,s.memory,w,1,Direction::EAST,false)==investment::Step::Outside);
  assert(w.actors[1].body==old&&w.food==0&&w.paid==0);}
 {Scene s;investment::Context context(s.bot,s.memory);auto original=strategy::Simulation{s.memory.body,{},true,6};
  auto f=investment::evaluate_split(s.bot,s.memory,original,2,context,0);
  assert(f.exhausted&&!f.complete&&f.food==0&&f.paid==0);}
 {Scene s;s.bot.length=8;s.memory.body.push_back({5,7});s.memory.body.push_back({4,7});
  s.bot.get_tile({5,7})->dragon_part=DragonPart{{5,7},2,Team::A,Direction::NORTH,false};
  s.bot.get_tile({4,7})->dragon_part=DragonPart{{4,7},2,Team::A,Direction::EAST,false};
  investment::World w;assert(investment::split_world(s.bot,s.memory,{s.memory.body,{},true,8},4,w));
  s.bot.get_tile({3,7})->pearl=true;s.bot.get_tile({2,7})->pearl=true;
  assert(investment::apply_action(s.bot,s.memory,w,1,{Direction::WEST,Direction::WEST}));
  assert(w.actors[1].length==5&&w.food==2&&w.paid==1);
  assert(w.records.back().start_length==4&&w.records.back().free_steps==1);}
 {Scene s;auto w=s.split();assert(investment::apply_action(s.bot,s.memory,w,1,{Direction::EAST}));
  assert(w.actors[1].body.back()==Position(5,6));
  assert(investment::step(s.bot,s.memory,w,0,Direction::SOUTH,false)==investment::Step::Blocked);
  assert(w.food==0&&w.paid==0);}
 std::cout<<"Joint world: split conservation, birth facing/quota, strict two-body collision, shared pearl ledger and unknown/budget passed\n";
}
