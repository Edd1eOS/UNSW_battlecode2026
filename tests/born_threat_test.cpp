#include "../opponents/generalist-v4/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
 Game board{64,64,64};Controller bot{0,Team::A,Direction::EAST,Vision{},64};strategy::Memory memory;
 Scene(Position head={28,32}) {
  game=&board;ct=&bot;bot.head.position=head;bot.length=5;bot.unit_count=10;
  std::vector<Tile> tiles;for(int dy=-3;dy<=3;++dy)for(int dx=-3;dx<=3;++dx)
   tiles.emplace_back(Position{(head.x+dx+64)%64,(head.y+dy+64)%64},std::nullopt,-1);
  bot.vision=Vision{std::move(tiles)};
 }
 void part(Position p,int id,Direction d,bool head=false,Team team=Team::B) {
  bot.get_tile(p)->dragon_part=DragonPart{p,id,team,d,head};
 }
 void observe(){memory.observe_map(bot,30);}
};
int main(){
 // Actual STAR M1249302 raw round30/UI round31 legal 7x7 geometry. Enemy35's
 // head is outside vision; only its two last body segments are observable.
 {Scene s;auto& bot=s.bot;
 bot.get_tile({25,29})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({28,29})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({29,29})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({29,29})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,29})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({25,30})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({25,30})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({27,30})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({28,30})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({29,30})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({29,30})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({30,30})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({30,30})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,30})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,30})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({25,31})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({26,31})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({27,31})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({27,31})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({28,31})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({29,31})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({29,31})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({30,31})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,31})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({27,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({27,32})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({28,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({29,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({30,32})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({31,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({27,33})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({28,33})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({29,33})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({30,33})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({30,33})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,33})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,33})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({30,34})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({31,34})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({31,34})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
bot.get_tile({28,35})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({31,35})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
bot.get_tile({31,35})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
 s.memory.body={{28,32},{27,32},{26,32},{25,32},{25,33}};
 s.part({28,32},0,Direction::EAST,true,Team::A);
 for(auto p:std::vector<Position>{{27,32},{26,32},{25,32}})s.part(p,0,Direction::EAST,false,Team::A);
 s.part({25,33},0,Direction::NORTH,false,Team::A);
 s.part({27,31},4,Direction::WEST,true,Team::A);s.part({28,31},4,Direction::WEST,false,Team::A);
 s.part({29,31},4,Direction::WEST,false,Team::A);s.part({29,30},4,Direction::SOUTH,false,Team::A);
 s.part({28,30},4,Direction::EAST,false,Team::A);s.part({28,29},4,Direction::SOUTH,false,Team::A);
 s.part({30,29},17,Direction::WEST,true);s.part({31,29},17,Direction::WEST);
 s.part({30,34},31,Direction::NORTH,true);s.part({30,35},31,Direction::NORTH);s.part({29,35},31,Direction::EAST);
 s.part({28,33},33,Direction::EAST,true);s.part({27,33},33,Direction::EAST);
 s.part({31,32},35,Direction::EAST);s.part({30,32},35,Direction::EAST);s.observe();
 auto births=born_threat::build(s.bot,s.memory);std::vector<bool> direct;planner::risks(s.bot,s.memory,&direct);
 assert(!direct[s.memory.index({29,32})]);assert(births.same_round_possible[s.memory.index({29,32})]);
 assert(!births.same_round_possible[s.memory.index({31,32})]);
 planner::State state;state.last_food=29;auto plan=planner::choose(s.bot,s.memory,state);
 auto sim=planner::initial(s.bot,s.memory);int n=0;for(auto d:plan.moves)assert(planner::step(s.bot,s.memory,sim,d,n++>=2));
 std::cout<<"STAR isolated legal observation: "<<plan.note<<" endpoint="<<sim.body.front().x<<","<<sim.body.front().y<<"\n";
 assert(!births.same_round_possible[s.memory.index(sim.body.front())]);
 assert(!direct[s.memory.index(sim.body.front())]);
 assert(sim.body.front()!=Position(29,32));
 // Isolated packet choice is evidence of the mechanism, not a replayed win.
 }
 // Partial headless body is not mistaken for exact enemy length two.
 {Scene s;s.part({30,32},35,Direction::EAST);s.part({31,32},35,Direction::EAST);s.observe();
 auto x=born_threat::build(s.bot,s.memory);assert(x.same_round_possible[s.memory.index({29,32})]);
 // A visible successor proves 30,32 is internal and cannot be split-tail head.
 s.part({29,32},35,Direction::EAST);s.observe();x=born_threat::build(s.bot,s.memory);
 assert(!x.same_round_possible[s.memory.index({30,31})]);}
 // Known full length3 cannot produce legal child2; full length4 can.
 {Scene s;s.part({28,30},7,Direction::EAST);s.part({29,30},7,Direction::EAST);s.part({30,30},7,Direction::EAST,true);s.observe();
 auto x=born_threat::build(s.bot,s.memory);assert(!x.same_round_possible[s.memory.index({28,29})]);
 s.part({30,30},7,Direction::EAST,false);s.part({31,30},7,Direction::EAST,true);s.observe();x=born_threat::build(s.bot,s.memory);
 assert(x.same_round_possible[s.memory.index({28,29})]);assert(!x.same_round_possible[s.memory.index({29,30})]);
 s.bot.get_tile({28,30})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};s.observe();x=born_threat::build(s.bot,s.memory);
 assert(!x.same_round_possible[s.memory.index({28,29})]);}
 // Already-acted parents are only next-round possibilities; friendlies excluded.
 {Scene s;s.bot.head.dragon_id=8;s.part({30,32},7,Direction::EAST);s.part({31,32},7,Direction::EAST);s.observe();
 auto x=born_threat::build(s.bot,s.memory);assert(!x.same_round_possible[s.memory.index({29,32})]);assert(x.next_round_possible[s.memory.index({29,32})]);
 s.part({30,32},9,Direction::EAST,false,Team::A);s.part({31,32},9,Direction::EAST,false,Team::A);s.observe();x=born_threat::build(s.bot,s.memory);
 assert(!x.same_round_possible[s.memory.index({29,32})]&&!x.next_round_possible[s.memory.index({29,32})]);}
 // Known portal destination participates; an unresolved mouth does not
 // fabricate a target or mark all unknown cells as attacks.
 {Scene s;s.part({30,32},35,Direction::EAST);s.part({31,32},35,Direction::EAST);
 s.bot.get_tile({30,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::PORTAL,7};
 s.bot.get_tile({28,30})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::PORTAL,7};s.observe();
 auto x=born_threat::build(s.bot,s.memory);assert(x.same_round_possible[s.memory.index({28,30})]);
 Scene unknown;unknown.part({30,32},35,Direction::EAST);unknown.part({31,32},35,Direction::EAST);
 unknown.bot.get_tile({30,32})->get_edge(Direction::NORTH)=Edge{true,EdgeType::PORTAL,7};unknown.observe();
 x=born_threat::build(unknown.bot,unknown.memory);assert(x.unresolved_portal);
 assert(!x.same_round_possible[unknown.memory.index({28,30})]);}
 // Distinct tiers prefer a possible-tail-free protected alternative. With no
 // such alternative the possible attack is still selectable; workers stay soft.
 {planner::Candidate safe,birth,head;birth.birth_possible=true;head.imminent=true;
 assert(planner::contact_tier(safe,true,2)>planner::contact_tier(birth,true,3));
 assert(planner::contact_tier(birth,true,3)>planner::contact_tier(head,true,3));
 assert(planner::contact_tier(safe,false,3)==planner::contact_tier(birth,false,3));
 planner::Candidate paid,free;paid.paid=1;paid.future.depth=8;free.future.depth=8;free.birth_possible=true;
 assert(!planner::capital_dominated(paid,free,8));}
 std::cout<<"born threat scenarios PASS\n";
}
