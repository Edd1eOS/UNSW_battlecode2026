#include "../opponents/generalist-exploration-v1/planner.hpp"
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
 // A dry worker may cross one unresolved portal without claiming food or safe
 // hidden terrain. The portal is one free step; the incoming reverse is banned.
 {RingPortal s;s.state.old_length=2;auto p=planner::choose(s.bot,s.memory,s.state);
 assert(p.kind==planner::Kind::UnknownPortal&&p.uncertain&&p.moves.size()==1&&p.moves[0]==Direction(Direction::EAST));
 assert(p.food==0&&p.paid==0&&s.state.exploration_budget.attempts==1&&s.state.exploration_budget.next_allowed==64);
 planner::remember(s.bot,s.memory,s.state,p,40);assert(s.state.pending.active);
 assert(s.memory.body.front()==Position(5,5)&&s.state.pending.prefix_history.front()==Position(5,5));
 std::cout<<"Dry worker opportunity: "<<p.note<<"\n";}
 // The same certified Queen ring remains preferable. Protected reserves and
 // last units, short dry periods, and cooldown retain the original policy.
 for(int guard=0;guard<5;++guard){RingPortal s{guard==0?1:3};s.state.old_length=2;
 if(guard==1)s.state.reserve=true;if(guard==2)s.bot.unit_count=1;
 if(guard==3)s.state.last_food=25;if(guard==4)s.state.exploration_budget.next_allowed=50;
 auto p=planner::choose(s.bot,s.memory,s.state);assert(p.kind==planner::Kind::Move&&p.moves[0]==Direction(Direction::NORTH));
 assert(s.state.exploration_budget.attempts==0);}
 // Any currently visible enemy part, including a headless possible tail,
 // prevents the dry override rather than bypassing head/birth risk contracts.
 {RingPortal s;s.state.old_length=2;s.bot.get_tile({7,7})->dragon_part=DragonPart{{7,7},8,Team::B,Direction::NORTH,false};s.memory.observe_map(s.bot,40);
 assert(!exploration::eligible(s.bot,s.memory,false,0,s.state.exploration_budget));
 auto p=planner::choose(s.bot,s.memory,s.state);assert(p.kind==planner::Kind::Move&&p.moves[0]==Direction(Direction::NORTH));}
 // Reachable current pearls and observed near spawns retain harvesting;
 // stale/unreachable pearls elsewhere are never invented as income.
 for(bool spawn:std::vector<bool>{false,true}){RingPortal s;s.state.old_length=2;
 if(spawn)s.bot.get_tile({5,4})->pearl_time=3;else s.bot.get_tile({5,4})->pearl=true;
 s.memory.observe_map(s.bot,40);auto p=planner::choose(s.bot,s.memory,s.state);
 assert(p.kind==planner::Kind::Move&&p.moves[0]==Direction(Direction::NORTH));assert(s.state.exploration_budget.attempts==0);
 if(!spawn)assert(p.food==1&&p.paid==0);}
 // Partial bodies cannot enter the exploration override; no unseen tail is
 // fabricated to claim complete-body safety.
 {RingPortal s;s.memory.body={{5,5}};assert(!exploration::eligible(s.bot,s.memory,false,0,s.state.exploration_budget));}
 // A portal on the proven incoming neck is never an exploration opportunity.
 {RingPortal s;s.bot.head.dir=Direction::WEST;assert(exploration::opportunities(s.bot,s.memory).empty());}
 std::cout<<"Bounded worker exploration scenarios PASS\n";
}
