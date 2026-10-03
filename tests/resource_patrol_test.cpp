#ifdef OLD_BASELINE
#include "../opponents/v64-paid-escape/forage.hpp"
#else
#include "../opponents/v70-resource-patrol/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main(){
 Game board{20,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};game=&board;ct=&bot;
 std::vector<Tile> all;for(int y=0;y<15;++y)for(int x=0;x<20;++x)all.emplace_back(Position{x,y},std::nullopt,-1);
 bot.vision=Vision{std::move(all)};bot.head.position={5,5};bot.length=2;bot.unit_count=5;
 strategy::Memory m;m.body={{5,5},{4,5}};m.observe_map(bot,90);
 std::vector<Tile> local;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)local.emplace_back(Position{x,y},std::nullopt,-1);
 bot.vision=Vision{std::move(local)};bot.get_tile({5,5})->dragon_part=bot.head;m.observe_map(bot,100);
 m.cells[m.index({12,5})].pearl=true;m.cells[m.index({12,5})].seen=60;
 forage::State s;auto exits=terrain::build(bot,m);int goal=forage::select_goal(bot,m,s,&exits);
#ifdef OLD_BASELINE
 assert(goal==-1);std::cout<<"Baseline discards old resource memory and has no goal.\n";
#else
 assert(goal==m.index({12,5}));std::cout<<"Revisit remembered resource while treating it as uncertain.\n";
#endif
}
