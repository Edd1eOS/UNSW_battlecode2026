#ifdef OLD_BASELINE
#include "../opponents/v80-portal-body-guard/forage.hpp"
#else
#include "../opponents/v94-portal-rescue/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main(){Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};game=&board;ct=&bot;std::vector<Tile> ts;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)ts.emplace_back(Position{x,y},std::nullopt,-1);bot.vision=Vision{std::move(ts)};bot.head.position={5,5};bot.length=4;bot.unit_count=5;bot.get_tile({5,5})->dragon_part=bot.head;for(auto d:Direction::get_direction_list())bot.get_tile({5,5})->get_edge(d).edge_type=EdgeType::KELP;bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,42};strategy::Memory m;m.body={{5,5},{4,5},{11,11},{10,11}};m.observe_map(bot,100);m.portals[42].push_back({{10,11},false});auto action=strategy::choose_action(bot,m,100,false);
#ifdef OLD_BASELINE
assert(action.child_size==0);std::cout<<"Old fallback misclassifies an own-body portal exit as an escape.\n";
#else
assert(action.child_size==2);std::cout<<"Blocked known portal triggers emergency split instead of certain self-collision.\n";
#endif
}
