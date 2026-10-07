#include "../opponents/generalist-investment-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(){game=&board;ct=&bot;bot.head.position={5,5};bot.length=8;bot.unit_count=10;
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
  bot.vision=Vision{std::move(tiles)};
  memory.body={{5,5},{4,5},{3,5},{3,6},{3,7},{4,7},{5,7},{5,6}};
  const std::vector<Direction> dirs={Direction::EAST,Direction::EAST,Direction::NORTH,Direction::NORTH,
   Direction::WEST,Direction::WEST,Direction::SOUTH,Direction::SOUTH};
  for(int i=0;i<8;++i)bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],2,Team::A,dirs[i],i==0};
 }
 void wall(Position p,Direction d){bot.get_tile(p)->get_edge(d)=Edge{false,EdgeType::KELP,-1};Position q=p.add_dir(d);
  if(auto* t=bot.get_tile(q))t->get_edge(d.get_opposite())=Edge{false,EdgeType::KELP,-1};}
 void observe(){memory.observe_map(bot,30);}
 investment::Forecast forecast(bool parent_food){
  if(parent_food){bot.get_tile({5,4})->pearl=true;bot.get_tile({5,3})->pearl=true;}
  else{bot.get_tile({6,6})->pearl=true;bot.get_tile({7,6})->pearl=true;}
  observe();investment::World w;
  assert(investment::split_world(bot,memory,planner::initial(bot,memory),2,w));
  assert(investment::apply_action(bot,memory,w,1,{Direction::EAST}));
  assert(investment::apply_action(bot,memory,w,0,{Direction::NORTH,Direction::NORTH}));
  assert(investment::apply_action(bot,memory,w,1,{Direction::EAST}));
  investment::Forecast f;f.valid=f.complete=true;f.world=w;f.food=w.food;f.paid=w.paid;
  return f;
 }
};
int main(){
 {Scene s;auto dispersed=s.forecast(false);planner::assess_investment_terminal(s.bot,s.memory,dispersed);
  assert(dispersed.food==2&&dispersed.paid==0&&dispersed.family_max_after==6);
  assert(planner::ordinary_investment_rejection(dispersed,false,false)==0);
  assert(planner::ordinary_investment_rejection(dispersed,true,false)==3);
  Scene t;auto concentrated=t.forecast(true);planner::assess_investment_terminal(t.bot,t.memory,concentrated);
  assert(concentrated.food==2&&concentrated.paid==0&&concentrated.family_max_after==8);
  assert(planner::ordinary_investment_rejection(concentrated,true,false)==0);
  std::cout<<"Same net +2: protected capital accepts 8+2, rejects 6+4; harvest permits both\n";
 }
 {Scene s;auto f=s.forecast(false);for(auto d:{Direction::NORTH,Direction::EAST,Direction::SOUTH})s.wall({7,6},d);
  s.observe();planner::assess_investment_terminal(s.bot,s.memory,f);
  assert(f.terminal[0].depth>=2&&f.terminal[1].depth==0);
  assert(!f.terminal[1].outside&&!f.terminal[1].portal&&!f.terminal[1].exhausted);
  assert(planner::ordinary_investment_rejection(f,false,false)==2);
  assert(planner::ordinary_investment_rejection(f,true,true)==0); // Last-unit rebuilding is unchanged.
  std::cout<<"Child eats two distinct pearls then terminal walls/old neck reject ordinary investment\n";
 }
 {Scene s;s.bot.get_tile({6,6})->pearl=true;s.bot.get_tile({7,6})->pearl=true;
  for(auto d:{Direction::NORTH,Direction::EAST,Direction::SOUTH})s.wall({7,6},d);
  s.observe();planner::State state;auto plan=planner::choose(s.bot,s.memory,state);
  std::cout<<plan.note<<"\n";
  assert(plan.kind!=planner::Kind::Split&&plan.note.find("investment_reject_terminal=1")!=std::string::npos);
  assert(plan.note.find("investment_reject_reason=2")!=std::string::npos);
  std::cout<<"Actual candidate gate rejects resource-bait child terminal and records reason\n";
 }
 {Scene s;s.bot.get_tile({6,6})->pearl=true;s.bot.get_tile({7,6})->pearl=true;s.observe();
  investment::World w;assert(investment::split_world(s.bot,s.memory,planner::initial(s.bot,s.memory),2,w));
  assert(investment::apply_action(s.bot,s.memory,w,1,{Direction::EAST}));
  assert(investment::apply_action(s.bot,s.memory,w,0,{Direction::NORTH}));
  assert(investment::apply_action(s.bot,s.memory,w,1,{Direction::EAST,Direction::EAST}));
  s.wall({8,6},Direction::NORTH);s.wall({8,6},Direction::SOUTH);s.observe();
  investment::Forecast f;f.complete=f.valid=true;f.world=w;f.food=w.food;f.paid=w.paid;
  planner::assess_investment_terminal(s.bot,s.memory,f);
  assert(f.terminal[1].depth==0&&f.terminal[1].outside);
  assert(planner::ordinary_investment_rejection(f,false,false)==0);
  f.terminal[1].outside=false;f.terminal[1].exhausted=true;
  assert(planner::ordinary_investment_rejection(f,false,false)==0);
  std::cout<<"Unknown boundary is unresolved evidence, ordinary harvest proposal remains eligible\n";
 }
 {Scene s;auto f=s.forecast(true);
  // The other actor, not ct's old parent tags, is the actual terminal blocker.
  const auto child_head=f.world.actors[1].body.front();
  auto parent=f.world.actors[0];parent.body={{7,5},{6,5},{5,5},{4,5},{3,5},{3,4},{4,4},{5,4}};parent.length=8;
  f.world.actors[0]=parent;s.wall(child_head,Direction::EAST);s.wall(child_head,Direction::SOUTH);s.observe();
  planner::assess_investment_terminal(s.bot,s.memory,f);
  assert(f.terminal[1].depth==0); // N is parent head, W child neck; neither is released early.
  std::cout<<"Terminal own neck and explicit other-body occupancy preserve strict collision order\n";
 }
}
