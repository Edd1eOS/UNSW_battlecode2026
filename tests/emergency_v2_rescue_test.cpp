#include "../opponents/generalist-emergency-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{20,20,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(std::deque<Position> body){game=&board;ct=&bot;bot.head.position=body.front();bot.length=body.size();bot.unit_count=3;
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){tiles.emplace_back(Position{x,y},std::nullopt,-1);
   for(auto d:Direction::get_direction_list())tiles.back().get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::KELP,-1};}
  bot.vision=Vision{std::move(tiles)};memory.body=body;
  for(int i=0;i<static_cast<int>(body.size());++i){bot.get_tile(body[i])->dragon_part=DragonPart{body[i],bot.head.dragon_id,Team::A,Direction::EAST,i==0};
   if(i){for(auto d:Direction::get_direction_list())if(body[i].add_dir(d)==body[i-1]){open(body[i],d);bot.get_tile(body[i])->dragon_part->dir=d;}}}
 }
 void open(Position p,Direction d){const Edge e{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::EMPTY,-1};
  bot.get_tile(p)->get_edge(d)=e;if(auto* t=bot.get_tile(p.add_dir(d)))t->get_edge(d.get_opposite())=e;}
 void refresh(){memory.observe_map(bot,40);}
 emergency::Assessment assess(int n){refresh();return emergency::assess(bot,memory,planner::initial(bot,memory),n);}
};
int main(){
 {Scene s({{5,5},{4,5},{3,5},{2,5}});auto a=s.assess(2);
  assert(a.complete&&a.facing_known&&a.child_no_first_move&&a.parent_no_first_move&&a.reject);
  planner::State state;auto plan=planner::choose(s.bot,s.memory,state);
#ifndef EMERGENCY_DISABLE
  assert(plan.kind==planner::Kind::Fallback&&plan.note.find("emergency_rejected=1")!=std::string::npos);
#else
  assert(plan.kind==planner::Kind::Split);
#endif
  std::cout<<"L2 parent+child known wall/neck closure, neither can split again\n";
  s.bot.unit_count=1;planner::State last_state;auto last_plan=planner::choose(s.bot,s.memory,last_state);
#ifndef EMERGENCY_DISABLE
  assert(last_plan.kind==planner::Kind::Fallback);
#endif
  // Rejection does not claim a rescue when both L2 actors have no action.

 }
 const std::deque<Position> hook{{5,5},{4,5},{3,5},{3,6},{4,6},{5,6}};
 {Scene s(hook);s.open({5,5},Direction::SOUTH);auto a=s.assess(2);assert(a.child_no_first_move&&!a.reject&&a.parent_future.unknown);
  // Parent may use this square after its child moves/dies, so waiting rescue remains.
  planner::State state;auto plan=planner::choose(s.bot,s.memory,state);assert(plan.kind==planner::Kind::Split);
  std::cout<<"Blocked child does not erase parent waiting/another split opportunity\n";
 }
 {Scene s(hook);s.open({5,5},Direction::SOUTH);s.bot.get_tile({5,6})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  auto a=s.assess(2);assert(a.child_future.portal&&!a.child_no_first_move&&!a.reject);
  std::cout<<"Unknown portal rescue is not known dead\n";
 }
 {Scene s(hook);s.open({5,5},Direction::SOUTH);s.open({5,6},Direction::EAST);s.bot.get_tile({6,6})->dragon_part=DragonPart{{6,6},9,Team::B,Direction::EAST,true};
  auto a=s.assess(2);assert(a.child_future.unknown&&!a.child_no_first_move&&!a.reject);
  std::cout<<"Foreign head may act before newborn; static occupation is unresolved\n";
 }
 {Scene s(hook);s.open({5,5},Direction::SOUTH);s.open({5,6},Direction::EAST);
  for(auto pd:std::vector<std::pair<Position,Direction>>{{{6,6},Direction::NORTH},{{6,5},Direction::SOUTH},{{4,6},Direction::SOUTH},{{4,7},Direction::NORTH}})
   s.bot.get_tile(pd.first)->get_edge(pd.second)=Edge{true,EdgeType::PORTAL,8};
  auto small=s.assess(2),large=s.assess(4);
  assert(!small.child_no_first_move&&!large.child_no_first_move);
  assert(small.child_future.depth==2&&large.child_future.depth==1);
  assert(small.child.body.front()==large.child.body.front());
  std::cout<<"Sizes share birth first-step geometry but release different tails for continuation\n";
 }
 {Scene s(hook);s.open({5,5},Direction::SOUTH);s.bot.head.dragon_id=0;for(auto& t:s.bot.vision.tiles)if(t.dragon_part)t.dragon_part->dragon_id=0;
  s.open({5,6},Direction::EAST);s.open({6,6},Direction::EAST);s.refresh();
  assert(strategy::emergency_split_size(s.bot)==2);planner::State state;auto plan=planner::choose(s.bot,s.memory,state);
  assert(plan.kind==planner::Kind::Split&&plan.action.child_size==2);
  std::cout<<"Unsealed Queen keeps original minimum-child rescue\n";
 }
 {Scene s({{5,5},{4,5},{4,6},{4,7},{3,7},{3,5}});
  for(auto pd:std::vector<std::pair<Position,Direction>>{{{3,7},Direction::NORTH},{{3,6},Direction::SOUTH},{{3,5},Direction::SOUTH},{{3,6},Direction::NORTH}})
   s.bot.get_tile(pd.first)->get_edge(pd.second)=Edge{true,EdgeType::PORTAL,9};
  s.bot.get_tile({3,5})->dragon_part->dir=Direction::NORTH;
  s.open({3,5},Direction::WEST);auto a=s.assess(2);
  assert(a.facing_known&&!a.child_no_first_move&&a.child_future.depth>=1);
  int budget=0;auto f=emergency::search(s.bot,s.memory,a.child,a.parent.body,true,Direction::NORTH,0,budget);
  assert(f.budget&&!emergency::closed_first(f));
  std::cout<<"Resolved portal child facing and exhausted evidence remain distinct\n";
 }
 {Scene s(hook);s.open({5,5},Direction::SOUTH);s.memory.body.resize(3);s.refresh();auto a=emergency::assess(s.bot,s.memory,planner::initial(s.bot,s.memory),2);
  assert(!a.complete&&!a.reject);std::cout<<"Partial body cannot certify closure\n";
 }
}
