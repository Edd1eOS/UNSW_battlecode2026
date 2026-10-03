#ifdef OLD_BASELINE
#include "../opponents/v76-collector-delivery/cooperation.hpp"
#else
#include "../opponents/v77-long-collector-delivery/cooperation.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main(){Game board{15,15,64};Controller bot{4,Team::A,Direction::EAST,Vision{},64};game=&board;ct=&bot;std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=8;strategy::Memory m;m.body={{5,5},{4,5},{3,5},{2,5},{1,5},{0,5},{14,5},{13,5}};for(auto p:m.body)if(auto* t=bot.get_tile(p))t->dragon_part=DragonPart{p,4,Team::A,Direction::EAST,p==Position(5,5)};m.observe_map(bot,100);auto scene=bot;
#ifdef OLD_BASELINE
assert(!cooperation::project(scene,m,{Direction::EAST}));std::cout<<"Old delivery projection rejects an own tail outside vision.\n";
#else
std::deque<Position> body;assert(cooperation::project(scene,m,{Direction::EAST},&body));assert(body.size()==8 && body.front()==Position(6,5) && body.back()==Position(14,5));assert(scene.get_length()==8);std::cout<<"Long receiver projection preserves its known body outside vision.\n";
#endif
}
