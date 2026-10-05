#include "../opponents/counterplay-prototype/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64}; Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game=&board;ct=&bot;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=2;bot.unit_count=4;
        bot.get_tile({5,5})->dragon_part=bot.head;
        bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},2,Team::A,Direction::EAST,false};
        memory.body={{5,5},{4,5}};memory.observe_map(bot,30);
    }
};
int main() {
    { Scene s;
      s.bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},4,Team::A,Direction::WEST,true};
      auto r=counterplay::endpoints(s.bot,s.memory);
      assert(r.contested(s.memory,{6,5}) && r.allies[s.memory.index({6,5})]==1);
      assert(!r.contested(s.memory,{5,4}));
      s.bot.get_tile({7,5})->dragon_part->dragon_id=0;
      assert(!counterplay::endpoints(s.bot,s.memory).contested(s.memory,{6,5})); }
    { Scene s;
      // 两条友军都想吃同一颗珍珠。旧版食物奖励可以盖过头碰风险。
      s.bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},4,Team::A,Direction::WEST,true};
      s.bot.get_tile({6,5})->pearl=true;s.memory.observe_map(s.bot,30);
      forage::State state;auto plan=forage::choose(s.bot,s.memory,state);
      assert(plan.action.child_size==0 && plan.moves.size()==1);
#if COUNTER_ENDPOINTS
      assert(plan.moves.front()!=Direction(Direction::EAST));
#else
      assert(plan.moves.front()==Direction(Direction::EAST));
#endif
      // 没有安全替代时仍保留风险路线，不输出非法等待或确定撞墙。
      s.bot.get_tile({5,5})->get_edge(Direction::NORTH).edge_type=EdgeType::KELP;
      s.bot.get_tile({5,5})->get_edge(Direction::SOUTH).edge_type=EdgeType::KELP;
      s.memory.observe_map(s.bot,30);forage::State trapped;
      auto fallback=forage::choose(s.bot,s.memory,trapped);
      assert(fallback.moves.size()==1 && fallback.moves.front()==Direction(Direction::EAST)); }
    { Scene s;
      s.bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},5,Team::B,Direction::WEST,true};
      assert(counterplay::endpoints(s.bot,s.memory).enemies[s.memory.index({6,5})]==1);
      s.bot.get_tile({7,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::KELP,-1};
      s.memory.observe_map(s.bot,30);
      assert(!counterplay::endpoints(s.bot,s.memory).contested(s.memory,{6,5})); }
    { Scene s;
      s.bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},5,Team::B,Direction::WEST,true};
      s.bot.get_tile({7,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({5,3})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      s.memory.observe_map(s.bot,30);
      auto r=counterplay::endpoints(s.bot,s.memory);
      assert(r.contested(s.memory,{4,3}));
      assert(!r.contested(s.memory,{6,5})); }
    assert(counterplay::continuation_class({6,false},true)<counterplay::continuation_class({2,false},false));
    assert(counterplay::continuation_class({6,false},true)>counterplay::continuation_class({1,false},false));
    assert(counterplay::continuation_class({0,true},false)==2);
    std::cout<<"Later head endpoints respect order, walls, portals and survival fallback.\n";
}
