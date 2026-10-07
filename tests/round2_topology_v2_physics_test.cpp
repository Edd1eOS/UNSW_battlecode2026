#include "../opponents/generalist-topology-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64}; Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory; planner::State state;
    Scene() {
        game=&board;ct=&bot;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=3;bot.unit_count=4;
        set_body({{5,5},{4,5},{3,5}});
    }
    void set_body(std::deque<Position> body) {
        for(auto& tile:bot.vision.tiles)tile.dragon_part.reset();
        memory.body=body;bot.length=static_cast<int>(body.size());bot.head.position=body.front();
        bot.get_tile(body.front())->dragon_part=bot.head;
        for(int i=1;i<static_cast<int>(body.size());++i)
            if(auto* t=bot.get_tile(body[i]))t->dragon_part=DragonPart{body[i],bot.get_id(),Team::A,Direction::EAST,false};
        memory.observe_map(bot,30);
    }
    void enemy(Position p,int id=3) {bot.get_tile(p)->dragon_part=DragonPart{p,id,Team::B,Direction::WEST,true};memory.observe_map(bot,30);}
};
struct PortalScene {
    Game board{48,24,64};Controller bot{202,Team::B,Direction::SOUTH,Vision{},64};
    strategy::Memory memory;planner::State state;
    PortalScene() {
        game=&board;ct=&bot;bot.length=4;bot.unit_count=4;
        memory.body={{33,15},{32,15},{32,16},{32,17}};
        view({33,15});
        for(auto p:memory.body)bot.get_tile(p)->dragon_part=DragonPart{p,202,Team::B,Direction::NORTH,p==Position(33,15)};
        bot.get_tile({33,15})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::PORTAL,42};
        memory.observe_map(bot,257);
    }
    void view(Position head) {
        std::vector<Tile> tiles;
        for(int dy=-3;dy<=3;++dy)for(int dx=-3;dx<=3;++dx)
            tiles.emplace_back(Position{(head.x+dx+48)%48,(head.y+dy+24)%24},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position=head;
        bot.get_tile(head)->dragon_part=bot.head;
    }
    void arrive(int length=4) {
        view({14,22});bot.length=length;
        bot.get_tile({14,22})->get_edge(Direction::NORTH)=Edge{true,EdgeType::PORTAL,42};
        memory.observe_map(bot,258);
        planner::reconcile_pending(bot,memory,state);
    }
};
int main() {
    // A paid destination pearl cannot finance a length-two dragon's step.
    { Scene s;s.set_body({{5,5},{4,5}});s.bot.get_tile({6,5})->pearl=true;
      auto sim=planner::initial(s.bot,s.memory);assert(!planner::step(s.bot,s.memory,sim,Direction::EAST,true));
      assert(sim.length==2&&sim.eaten.empty()); }
    // Payment is after collision: even the old tail remains solid.
    { Scene s;s.set_body({{5,5},{4,5},{4,4},{5,4}});s.bot.get_tile({5,4})->pearl=true;
      auto sim=planner::initial(s.bot,s.memory);assert(!planner::step(s.bot,s.memory,sim,Direction::NORTH,true));
      assert(sim.length==4&&sim.body.size()==4&&sim.eaten.empty()); }
    // Free quota is fixed at action-start L3: a free pearl does not buy
    // another free step. The second pearl and actual paid cost cancel.
    { Scene s;s.bot.get_tile({6,5})->pearl=true;s.bot.get_tile({7,5})->pearl=true;
      auto sim=planner::initial(s.bot,s.memory);const int free=(s.bot.get_length()+3)/4;
      assert(free==1&&planner::step(s.bot,s.memory,sim,Direction::EAST,false));
      assert(sim.length==4&&planner::step(s.bot,s.memory,sim,Direction::EAST,true));
      assert(sim.length==4&&sim.eaten.size()==2&&sim.body.size()==4); }
    // The selected plan can harvest visible food but never deliberately
    // trades against an ordinary worker or walks through another body.
    { Scene s;s.enemy({6,5});s.bot.get_tile({5,4})->pearl=true;s.memory.observe_map(s.bot,30);
      auto p=planner::choose(s.bot,s.memory,s.state);assert(p.kind==planner::Kind::Move);
      assert(!p.moves.empty());auto sim=planner::initial(s.bot,s.memory);int n=0;
      for(auto d:p.moves)assert(planner::step(s.bot,s.memory,sim,d,n++>=(s.bot.get_length()+3)/4));
      assert(p.food==static_cast<int>(sim.eaten.size())&&p.paid==std::max(0,n-1));
      assert(std::find(sim.eaten.begin(),sim.eaten.end(),Position{5,4})!=sim.eaten.end()); }
    // No population-based demotion of a previously grown reserve.
    { Scene s;s.bot.length=8;planner::update_role(s.bot,s.memory,s.state);assert(s.state.reserve);
      s.bot.unit_count=2;s.bot.length=6;planner::update_role(s.bot,s.memory,s.state);assert(s.state.reserve);
      auto p=planner::choose(s.bot,s.memory,s.state);assert(p.kind!=planner::Kind::Split); }
    { Scene s;s.memory.reserve_worker=true;s.memory.splits_done=1;
      planner::update_role(s.bot,s.memory,s.state);assert(s.state.reserve); }
    // Ordinary harvesters can still replicate; the parent keeps four of six
    // segments and the reversed-tail child is checked for an immediate exit.
    { Scene s;s.set_body({{5,5},{4,5},{3,5},{3,6},{4,6},{5,6}});s.bot.unit_count=2;
      auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::Split&&p.action.child_size==2&&!s.state.reserve); }
    // Reversed old-tail child head and direction, as the official split.
    { Scene s;strategy::Simulation child;child.body={{3,5},{4,5}};child.length=2;child.complete=true;
      Direction facing=Direction::NORTH;assert(planner::child_facing(s.bot,s.memory,child,facing));
      assert(facing==Direction(Direction::WEST)); }
    // Budget exhaustion is uncertainty, not confirmed closure.
    { Scene s;auto sim=planner::initial(s.bot,s.memory);int budget=0;
      auto f=planner::continuation(s.bot,s.memory,sim,{},0,6,budget);
      assert(f.exhausted&&!f.outside&&!f.portal&&f.depth==0); }
    // Preserve a free-prefix pearl through deeper safe continuation.
    { Scene s;s.bot.get_tile({6,5})->pearl=true;s.memory.observe_map(s.bot,30);
      auto sim=planner::initial(s.bot,s.memory);int budget=140;
      auto f=planner::continuation(s.bot,s.memory,sim,{},0,6,budget);
      assert(f.depth==6&&f.next_free_food==1); }
    // A trapped food branch must not contribute to another safe route.
    { Scene s;auto* t=s.bot.get_tile({5,4});t->pearl=true;
      for(auto d:Direction::get_direction_list())if(d!=Direction(Direction::SOUTH))t->get_edge(d)=Edge{false,EdgeType::KELP,-1};
      s.memory.observe_map(s.bot,30);auto sim=planner::initial(s.bot,s.memory);int budget=140;
      auto f=planner::continuation(s.bot,s.memory,sim,{},0,6,budget);
      assert(f.depth==6&&f.next_free_food==0); }
    // A pending unknown final landing preserves the known body/prefix.
    { Scene s;planner::Plan p{{Direction::EAST,0},{Direction::EAST,Direction::EAST},
          "unknown final landing",planner::Kind::Move,0,0,true};
      planner::remember(s.bot,s.memory,s.state,p,30);
      assert(s.state.pending.active&&s.state.pending.prefix_history.front()==Position(6,5));
      assert(s.memory.body.front()==Position(5,5)); }
    // Direct-head avoidance does not turn summed soft reach into certain death.
    { Scene s;s.enemy({7,5});
      for(auto p:std::vector<Position>{{7,4},{7,3}})
          s.bot.get_tile(p)->dragon_part=DragonPart{p,3,Team::B,Direction::SOUTH,false};
      s.memory.observe_map(s.bot,30);std::vector<bool> imminent;auto risk=planner::risks(s.bot,s.memory,&imminent);
      assert(imminent[s.memory.index({6,5})]);
      assert(!imminent[s.memory.index({5,5})]&&risk[s.memory.index({5,5})]>0);
      planner::Candidate direct,unknown,soft,closed;direct.imminent=true;soft.risk=1.4;
      assert(planner::contact_tier(direct,true,3)==0&&planner::contact_tier(unknown,true,1)==1);
      assert(planner::contact_tier(soft,true,3)==1&&planner::contact_tier(closed,true,0)==0);
      assert(planner::contact_tier(unknown,false,1)==0); }
    // A visible friendly fixed Queen is necessary for a two-unit trade.
    { Scene s;s.bot.unit_count=2;s.enemy({6,5},1);
      auto p=planner::choose(s.bot,s.memory,s.state);assert(p.kind!=planner::Kind::QueenTrade);
      s.bot.get_tile({7,7})->dragon_part=DragonPart{{7,7},0,Team::A,Direction::NORTH,true};
      s.memory.observe_map(s.bot,30);p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::QueenTrade&&p.moves.size()==1&&p.moves[0]==Direction(Direction::EAST)); }
    // Actual Maze gateway coordinates: S(33,15)->(14,22), then N returns
    // to the previous head, now an off-vision neck. Unknown food changes tail
    // length, never whether that neck remains occupied.
    for(int finalLength:std::vector<int>{4,5}) {
      PortalScene s;auto old=s.memory.body;
      planner::Plan p{{Direction::SOUTH,0},{Direction::SOUTH},"unresolved gateway",planner::Kind::UnknownPortal,0,0,true};
      planner::remember(s.bot,s.memory,s.state,p,257);assert(s.state.pending.active);
      s.arrive(finalLength);assert(!s.state.pending.active);
      assert(s.memory.body.size()==static_cast<std::size_t>(finalLength));
      assert(s.memory.body.front()==Position(14,22)&&s.memory.body[1]==Position(33,15));
      assert(s.memory.body.back()==old[finalLength==5?3:2]);
      auto sim=planner::initial(s.bot,s.memory);
      assert(sim.complete&&!planner::step(s.bot,s.memory,sim,Direction::NORTH,false));
      auto selected=planner::choose(s.bot,s.memory,s.state);
      assert(selected.kind==planner::Kind::Move&&selected.moves.front()!=Direction(Direction::NORTH));
    }
    // A known free prefix plus an unknown paid final step commits the actual
    // length instead of dropping an unverified tail before observation.
    for(int finalLength:std::vector<int>{3,4}) {
      PortalScene s;s.bot.get_tile({33,15})->get_edge(Direction::SOUTH)=Edge{};
      s.bot.get_tile({34,15})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,77};
      s.memory.observe_map(s.bot,257);
      planner::Plan p{{Direction::EAST,0},{Direction::EAST,Direction::EAST},"paid unknown final",planner::Kind::Move,0,1,true};
      planner::remember(s.bot,s.memory,s.state,p,257);
      s.view({14,22});s.bot.length=finalLength;
      s.bot.get_tile({14,22})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,77};
      s.memory.observe_map(s.bot,258);planner::reconcile_pending(s.bot,s.memory,s.state);
      assert(s.memory.body.size()==static_cast<std::size_t>(finalLength)&&s.memory.body[1]==Position(34,15));
      auto sim=planner::initial(s.bot,s.memory);
      assert(!planner::step(s.bot,s.memory,sim,Direction::WEST,false));
    }
    // Repeated gateways preserve the entire guaranteed head history.
    { PortalScene s;planner::Plan p{{Direction::SOUTH,0},{Direction::SOUTH},"gateway",planner::Kind::UnknownPortal,0,0,true};
      planner::remember(s.bot,s.memory,s.state,p,257);s.arrive();
      s.bot.get_tile({14,22})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::PORTAL,88};
      s.memory.observe_map(s.bot,258);planner::remember(s.bot,s.memory,s.state,p,258);
      s.view({20,5});s.bot.get_tile({20,5})->get_edge(Direction::NORTH)=Edge{true,EdgeType::PORTAL,88};
      s.memory.observe_map(s.bot,259);planner::reconcile_pending(s.bot,s.memory,s.state);
      assert(s.memory.body.size()==4&&s.memory.body[1]==Position(14,22)&&s.memory.body[2]==Position(33,15));
      auto sim=planner::initial(s.bot,s.memory);assert(!planner::step(s.bot,s.memory,sim,Direction::NORTH,false)); }
    // A partial old body remains partial after observation, while its known
    // neck still forbids an immediate reverse gateway.
    { PortalScene s;s.memory.body.resize(2);
      planner::Plan p{{Direction::SOUTH,0},{Direction::SOUTH},"partial gateway",planner::Kind::UnknownPortal,0,0,true};
      planner::remember(s.bot,s.memory,s.state,p,257);s.arrive();
      auto sim=planner::initial(s.bot,s.memory);assert(!sim.complete&&sim.body.size()==3);
      assert(!planner::step(s.bot,s.memory,sim,Direction::NORTH,false)); }
    // Actual feedback inconsistent with an already resolved exit cannot
    // silently commit the pending prediction as a complete body.
    { PortalScene s;s.memory.portals[42].push_back({{14,21},true});
      planner::Plan p{{Direction::SOUTH,0},{Direction::SOUTH},"known far exit",planner::Kind::Move,0,0,true};
      planner::remember(s.bot,s.memory,s.state,p,257);assert(s.state.pending.expected_head_known);
      s.view({15,22});planner::reconcile_pending(s.bot,s.memory,s.state);
      assert(!s.state.pending.active&&s.memory.body.empty()); }
    // Known paid prefix plus unknown paid end: first pearl is real prefix
    // income; both costs use the fixed action-start free quota.
    for(int finalLength:std::vector<int>{3,4}) {
      PortalScene s;s.bot.get_tile({33,15})->get_edge(Direction::SOUTH)=Edge{};
      s.bot.get_tile({34,15})->pearl=true;
      s.bot.get_tile({35,15})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,99};
      s.memory.observe_map(s.bot,257);
      planner::Plan p{{Direction::EAST,0},{Direction::EAST,Direction::EAST,Direction::EAST},"paid prefix and end",planner::Kind::Move,1,2,true};
      planner::remember(s.bot,s.memory,s.state,p,257);
      assert(s.state.pending.minimum_length==3&&s.state.pending.maximum_length==4);
      s.view({14,22});s.bot.length=finalLength;
      s.bot.get_tile({14,22})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,99};
      s.memory.observe_map(s.bot,258);planner::reconcile_pending(s.bot,s.memory,s.state);
      assert(s.memory.body.size()==static_cast<std::size_t>(finalLength)&&s.memory.body[1]==Position(35,15));
      auto sim=planner::initial(s.bot,s.memory);assert(!planner::step(s.bot,s.memory,sim,Direction::WEST,false)); }
    // Devil B r146 failure shape: a trapped L2 worker has a friendly Queen
    // north and its own neck west. The fallback must lose only this worker.
    { Scene s;s.set_body({{5,5},{4,5}});
      s.bot.get_tile({5,4})->dragon_part=DragonPart{{5,4},0,Team::A,Direction::SOUTH,true};
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
      s.bot.get_tile({5,5})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
      s.memory.observe_map(s.bot,30);auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::Fallback&&p.moves.front()!=Direction(Direction::NORTH));
      assert(p.note.find("no_confirmed_escape")!=std::string::npos); }
    // Static finite closure is weak evidence; unresolved/budget-limited
    // continuation wins this evidence tier, without being called safe.
    { planner::Future finite{4,false,false,false},portal{0,false,true,false},budget{1,false,false,true},full{6,false,false,false};
      assert(planner::future_grade(finite,6)<planner::future_grade(portal,6));
      assert(planner::future_grade(finite,6)<planner::future_grade(budget,6));
      assert(planner::future_grade(full,6)>planner::future_grade(portal,6)); }
    // Capital guard is a dominance rule, not a blanket acceleration ban.
    { planner::Candidate paid,free;paid.paid=1;paid.future.depth=6;free.future.depth=6;
      assert(planner::capital_dominated(paid,free,6));
      paid.future.next_free_food=1;assert(!planner::capital_dominated(paid,free,6));
      paid.future.next_free_food=0;free.enemy_risk=0.35;assert(!planner::capital_dominated(paid,free,6));
      free.enemy_risk=0;free.future={2,false,false,false};assert(!planner::capital_dominated(paid,free,6));
      free.future.depth=6;free.imminent=true;assert(!planner::capital_dominated(paid,free,6));
      free.imminent=false;paid.food=1;assert(!planner::capital_dominated(paid,free,6)); }
    // A lone ordinary worker receives the same contact and unknown-step
    // protection as a scoring reserve, without becoming a permanent reserve.
    { Scene s;s.bot.unit_count=1;assert(planner::protected_asset(s.bot,s.state));
      assert(!s.state.reserve);s.bot.unit_count=2;assert(!planner::protected_asset(s.bot,s.state)); }
    // Stripes last-survivor shape: E endpoint is directly reachable by the
    // visible enemy Queen; W is a resolved portal with unresolved farther
    // continuation. Unknown does not mean safe, but avoids direct contact.
    { PortalScene s;s.bot.head.dragon_id=2;s.bot.head.team=Team::A;s.bot.head.dir=Direction::SOUTH;
      s.view({17,8});s.bot.length=2;s.bot.unit_count=1;s.memory.body={{17,8},{17,7}};
      s.bot.get_tile({17,7})->dragon_part=DragonPart{{17,7},2,Team::A,Direction::SOUTH,false};
      auto* head=s.bot.get_tile({17,8});head->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
      head->get_edge(Direction::SOUTH)=Edge{true,EdgeType::KELP,-1};
      head->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,120};
      s.bot.get_tile({17,9})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,120};
      s.bot.get_tile({16,9})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,120};
      s.bot.get_tile({19,8})->dragon_part=DragonPart{{19,8},1,Team::B,Direction::SOUTH,true};
      s.bot.get_tile({19,7})->dragon_part=DragonPart{{19,7},1,Team::B,Direction::SOUTH,false};
      for(auto d:std::vector<Direction>{Direction::NORTH,Direction::WEST})
          s.bot.get_tile({16,9})->get_edge(d)=Edge{d==Direction(Direction::NORTH),EdgeType::KELP,-1};
      s.memory.portals.clear();s.memory.observe_map(s.bot,40);
      auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::Move&&p.moves.front()==Direction(Direction::WEST));
      assert(p.note.find("role=LAST")!=std::string::npos); }
    // A fresh Maze child can have only its head visible: incoming DIR W
    // still proves unresolved portal E returns to its old off-vision neck.
    for(int length:std::vector<int>{2,50}) for(bool known:std::vector<bool>{false,true}) {
      PortalScene s;s.bot.head.dir=Direction::WEST;s.bot.length=length;
      s.memory.body={{33,15}};s.bot.get_tile({33,15})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,999};
      for(auto d:std::vector<Direction>{Direction::NORTH,Direction::SOUTH})
        s.bot.get_tile({33,15})->get_edge(d)=Edge{true,EdgeType::KELP,-1};
      s.bot.get_tile({33,15})->get_edge(Direction::WEST)=Edge{false,EdgeType::EMPTY,-1};
      s.memory.observe_map(s.bot,257);
      if(known)s.memory.portals[999].push_back({{40,15},false});
      auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.moves.empty()||p.moves.front()!=Direction(Direction::EAST)); }
    // Paid loss remains legal when every free exit is directly threatened.
    { Scene s;s.bot.head.dragon_id=0;s.set_body({{5,5},{4,5},{4,4},{5,4}});
      s.bot.get_tile({6,6})->dragon_part=DragonPart{{6,6},3,Team::B,Direction::SOUTH,true};
      s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},3,Team::B,Direction::SOUTH,false};
      s.bot.get_tile({6,4})->dragon_part=DragonPart{{6,4},3,Team::B,Direction::SOUTH,false};
      s.memory.observe_map(s.bot,30);auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::Move&&p.paid>p.food&&p.note.find("direct_contact=0")!=std::string::npos);
      auto sim=planner::initial(s.bot,s.memory);int index=0;
      for(auto d:p.moves)assert(planner::step(s.bot,s.memory,sim,d,index++>=1)); }
    // A complete emergency parent no longer invents outside evidence.
    // Child occupies the old tail; parent has no modeled continuation.
    { Scene s;s.bot.head.dragon_id=0;s.bot.get_tile({5,5})->dragon_part=s.bot.head;
      s.set_body({{5,5},{4,5},{3,5},{3,6},{4,6},{5,6}});
      s.bot.get_tile({5,5})->get_edge(Direction::NORTH)=Edge{true,EdgeType::KELP,-1};
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::KELP,-1};
      s.memory.observe_map(s.bot,30);assert(strategy::emergency_split_size(s.bot)>0);
      auto p=planner::choose(s.bot,s.memory,s.state);
      assert(p.kind==planner::Kind::Split&&!p.uncertain&&p.note.find("outside=0")!=std::string::npos); }
    std::cout<<"V3 physics, pending bodies, capital dominance, protected last survivor and fresh-child neck passed\n";
}
