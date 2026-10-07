#include "../opponents/generalist-v5/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct RingPortal {
 Game board{20,20,64};Controller bot{3,Team::A,Direction::EAST,Vision{},64};
 strategy::Memory memory;planner::State state;
 RingPortal(int id=3){
  game=&board;ct=&bot;bot.head.dragon_id=id;bot.length=2;bot.unit_count=3;bot.head.position={5,5};
  std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){
   tiles.emplace_back(Position{x,y},std::nullopt,-1);for(auto d:Direction::get_direction_list())
    tiles.back().get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::KELP,-1};
  }
  bot.vision=Vision{std::move(tiles)};
  open({5,5},Direction::NORTH);open({5,4},Direction::WEST);open({4,4},Direction::SOUTH);open({4,5},Direction::EAST);
  bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
  bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
  bot.get_tile({5,5})->dragon_part=bot.head;
  bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},id,Team::A,Direction::EAST,false};
  memory.body={{5,5},{4,5}};memory.observe_map(bot,40);state.last_food=0;
 }
 void open(Position from,Direction d){bot.get_tile(from)->get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction(Direction::SOUTH),EdgeType::EMPTY,-1};
  bot.get_tile(from.add_dir(d))->get_edge(d.get_opposite())=bot.get_tile(from)->get_edge(d);}
};
int main(){
 // A physically verified length2 four-cell ring and a visible unknown portal.
 // The partner mouth is never present in the input or Memory. Unknown exit
 // safety is deliberately not claimed; this tests objective ordering only.
 for(int id:std::vector<int>{1,3}){
  RingPortal s{id};Position to;assert(!s.memory.destination(s.bot,{5,5},Direction::EAST,to));
  auto sim=planner::initial(s.bot,s.memory);assert(planner::step(s.bot,s.memory,sim,Direction::NORTH,false));
  int budget=140;int horizon=id<=1?8:6;auto future=planner::continuation(s.bot,s.memory,sim,{},0,horizon,budget);
  assert(future.depth==horizon&&planner::future_grade(future,horizon)==3);
  planner::Future unknown{0,true,false,false};assert(planner::future_grade(unknown,horizon)==2);
  auto plan=planner::choose(s.bot,s.memory,s.state);
  assert(plan.kind==planner::Kind::Move&&plan.moves.size()==1&&plan.moves[0]==Direction(Direction::NORTH));
  std::cout<<(id<=1?"Queen":"Worker")<<" known ring beats unknown portal: "<<plan.note<<"\n";
 }
 std::cout<<"V5 dry-ring/portal ordering causal fixture PASS\n";
}
