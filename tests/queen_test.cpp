#include "../bot/strategy.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};
    Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game=&board; ct=&bot;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y});
        bot.vision=Vision{std::move(tiles)}; bot.head.position={5,5};
        bot.get_tile({5,5})->dragon_part=bot.head;
    }
    void wall(Position p,Direction d) { bot.get_tile(p)->get_edge(d).edge_type=EdgeType::KELP; }
    void body(int id=0) {
        bot.head.dragon_id=id; bot.length=12;
        memory.body={{5,5},{5,4},{5,3},{4,3},{3,3},{3,4},{3,5},{3,6},{4,6},{5,6},{6,6},{7,6}};
        for(std::size_t i=0;i<memory.body.size();++i)
            bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],id,Team::A,Direction::NORTH,i==0};
        memory.observe_map(bot,100);
    }
};
int main() {
    { Scene s; s.body(); auto a=strategy::choose_action(s.bot,s.memory,100);
      assert(a.child_size==3 && s.bot.length-a.child_size>=8);
      assert(strategy::choose_action(s.bot,s.memory,400).child_size==0);
      s.bot.unit_count=3; assert(strategy::choose_action(s.bot,s.memory,100).child_size==0);
      s.bot.unit_count=1; s.memory.last_split_round=95;
      assert(strategy::choose_action(s.bot,s.memory,100).child_size==0); }
    { Scene s; s.body(2); assert(strategy::choose_action(s.bot,s.memory,100).child_size==6);
      s.bot.unit_count=16; assert(strategy::choose_action(s.bot,s.memory,100).child_size==0);
      s.bot.unit_count=1; s.memory.body.pop_back();
      assert(strategy::choose_action(s.bot,s.memory,100).child_size==0); }
    { Scene s; s.body(2); s.memory.observe(s.bot);
      assert(s.memory.reserve_worker);
      auto action=strategy::choose_action(s.bot,s.memory,100);
      assert(action.child_size==4);
      strategy::remember_action(s.bot,s.memory,action,{},100);
      assert(s.memory.splits_done==1);
      assert(strategy::choose_action(s.bot,s.memory,140).child_size==0); }
    { Scene s; s.body(); for(auto d:Direction::get_direction_list()) s.wall({5,5},d);
      assert(strategy::choose_action(s.bot,s.memory,100).child_size==10);
      s.bot.head.dragon_id=1; assert(strategy::emergency_split_size(s.bot)==10);
      s.bot.head.dragon_id=2; assert(strategy::emergency_split_size(s.bot)==10); }
    { Scene s; s.body();
      for(auto d:Direction::get_direction_list()) s.wall({5,5},d);
      s.bot.get_tile({5,5})->get_edge(Direction::EAST).edge_type=EdgeType::EMPTY;
      s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},8,Team::A,Direction::EAST,false};
      assert(strategy::emergency_split_size(s.bot)==2); // Another dragon may move away.
      s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},0,Team::A,Direction::WEST,false};
      assert(strategy::emergency_split_size(s.bot)==10); // Our own neck cannot leave first.
    }
    { Scene s;
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({7,7})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({8,7})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      s.memory.observe(s.bot); assert(s.memory.portals[7].size()==2);
      Position p; assert(s.memory.destination(s.bot,{5,5},Direction::EAST,p) && p==Position(8,7));
      assert(s.memory.destination(s.bot,{6,5},Direction::WEST,p) && p==Position(7,7));
      s.bot.get_tile({8,7})->pearl=true; s.memory.observe(s.bot);
      assert(strategy::choose_move(s.bot,s.memory)==Direction(Direction::EAST));
      strategy::Simulation state{{Position{5,5}}, {}, false, 3};
      assert(strategy::simulate_step(s.bot,state,Direction::EAST,&s.memory));
      assert(state.body.front()==Position(8,7) && state.length==4);
      s.bot.get_tile({8,7})->dragon_part=DragonPart{{8,7},2,Team::A,Direction::WEST,false};
      assert(strategy::choose_move(s.bot,s.memory)!=Direction(Direction::EAST)); }
    { Scene s;
      s.bot.get_tile({5,5})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::PORTAL,9};
      s.bot.get_tile({7,7})->get_edge(Direction::SOUTH)=Edge{true,EdgeType::PORTAL,9};
      s.memory.observe(s.bot); Position p;
      assert(s.memory.destination(s.bot,{5,5},Direction::SOUTH,p) && p==Position(7,8)); }
    { Scene s;
      // 跨地图边界的门，同一条边的两侧必须合并。
      auto a=strategy::Atlas::mouth({0,5},Direction::WEST);
      auto b=strategy::Atlas::mouth({14,5},Direction::EAST);
      assert(a.base==b.base && a.horizontal==b.horizontal); }
    { Scene s;
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
      s.memory.observe(s.bot); Position p;
      assert(!s.memory.destination(s.bot,{5,5},Direction::EAST,p));
      assert(strategy::choose_move(s.bot,s.memory)!=Direction(Direction::EAST));
      s.bot.head.dragon_id=2; s.memory.remember({5,5}); s.memory.remember({5,5});
      assert(strategy::choose_move(s.bot,s.memory)==Direction(Direction::EAST)); }
    { Scene s;
      s.bot.get_tile({8,5})->pearl=true; s.memory.observe(s.bot);
      // 旧视野以外只保留地形和短期珍珠记忆，不保留单位阻挡。
      s.bot.vision=Vision{std::vector<Tile>{Tile{Position{5,5}}}};
      double fresh=s.memory.route_value(s.bot,{8,5});
      s.memory.now+=13; assert(s.memory.route_value(s.bot,{8,5})<fresh);
      assert(s.memory.cell({8,5})->known); }
    { Scene s; s.bot.length=5; s.memory.body={{5,5},{4,5},{3,5},{3,4},{3,3}};
      for(std::size_t i=1;i<s.memory.body.size();++i)
          s.bot.get_tile(s.memory.body[i])->dragon_part=DragonPart{s.memory.body[i],0,Team::A,Direction::EAST,false};
      s.bot.get_tile({7,5})->pearl=true; s.memory.observe_map(s.bot,10);
      auto moves=strategy::plan_moves(s.bot,s.memory,Direction::EAST);
      assert(moves.size()==2 && moves[1]==Direction(Direction::EAST));
      strategy::remember_action(s.bot,s.memory,{Direction::EAST,0},moves,10);
      assert(s.memory.body.front()==Position(7,5) && s.memory.body.size()==6);
      s.bot.length=4; assert(strategy::plan_moves(s.bot,s.memory,Direction::EAST).size()==1); }
    std::cout<<"Queen roles, split limits, portal routing, memory expiry, and free sprint checks passed\n";
}
