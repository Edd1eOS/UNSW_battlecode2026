#include "../opponents/generalist-v1/planner.hpp"
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
    // Unknown multi-step final landing cannot leave a stale complete body.
    { Scene s;planner::Plan p{{Direction::EAST,0},{Direction::EAST,Direction::EAST},
          "unknown final landing",planner::Kind::Move,0,0,true};
      planner::remember(s.bot,s.memory,p,30);assert(s.memory.body.empty()); }
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
    std::cout<<"Generalist: old-tail collision, paid order/quota, food ledger, worker collision veto, persistent reserve, split facing and explicit uncertainty passed\n";
}
