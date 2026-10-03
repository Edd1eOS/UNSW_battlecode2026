#ifdef OLD_BASELINE
#include "../opponents/v80-portal-body-guard/forage.hpp"
#else
#include "../opponents/v84-profitable-trades/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main(){Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};game=&board;ct=&bot;std::vector<Tile> ts;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)ts.emplace_back(Position{x,y},std::nullopt,-1);bot.vision=Vision{std::move(ts)};bot.head.position={5,5};bot.length=2;bot.unit_count=20;bot.get_tile({5,5})->dragon_part=bot.head;bot.get_tile({4,5})->dragon_part=DragonPart{{4,5},2,Team::A,Direction::EAST,false};bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},3,Team::B,Direction::WEST,true};bot.get_tile({7,5})->dragon_part=DragonPart{{7,5},3,Team::B,Direction::WEST,false};strategy::Memory m;m.body={{5,5},{4,5}};m.observe_map(bot,120);auto attack=forage::attack_queen(bot,m,true);
#ifdef OLD_BASELINE
assert(!attack.empty());std::cout<<"Baseline deliberately trades length two for length two.\n";
#else
assert(attack.empty());for(auto p:std::vector<Position>{{7,4},{6,4},{6,3},{7,3}})bot.get_tile(p)->dragon_part=DragonPart{p,3,Team::B,Direction::SOUTH,false};m.observe_map(bot,121);attack=forage::attack_queen(bot,m,true);assert(attack.size()==1 && attack[0]==Direction(Direction::EAST));forage::State state;state.collector=true;auto plan=forage::choose(bot,m,state);assert(plan.note.find("ATTACK_LARGE_WORKER")==std::string::npos);std::cout<<"Scout rejects equal trade but can trade two for six; collector retains length.\n";
#endif
}
