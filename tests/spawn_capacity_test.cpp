#ifdef OLD_BASELINE
#include "../opponents/v64-paid-escape/forage.hpp"
#else
#include "../opponents/v71-spawn-capacity/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;
int main(){Game board{15,15,64};Controller bot{0,Team::A,Direction::NORTH,Vision{},64};game=&board;ct=&bot;
 std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){tiles.emplace_back(Position{x,y},std::nullopt,-1);for(auto d:Direction::get_direction_list())tiles.back().get_edge(d).edge_type=EdgeType::KELP;}
 bot.vision=Vision{std::move(tiles)};auto open=[&](Position p,Direction d){bot.get_tile(p)->get_edge(d).edge_type=EdgeType::EMPTY;bot.get_tile(p.add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::EMPTY;};
 open({5,5},Direction::EAST);open({6,5},Direction::SOUTH);open({6,6},Direction::WEST);open({5,6},Direction::NORTH);
 bot.head.position={5,5};bot.length=3;bot.unit_count=5;bot.get_tile({5,5})->dragon_part=bot.head;bot.get_tile({5,6})->dragon_part=DragonPart{{5,6},0,Team::A,Direction::NORTH,false};bot.get_tile({6,6})->dragon_part=DragonPart{{6,6},0,Team::A,Direction::WEST,false};bot.get_tile({5,6})->pearl_time=4;
 strategy::Memory m;m.body={{5,5},{5,6},{6,6}};m.observe_map(bot,100);forage::State s;auto p=forage::choose(bot,m,s);
#ifdef OLD_BASELINE
 assert(p.moves.size()==1);std::cout<<"Baseline leaves no buffer for imminent chamber growth.\n";
#else
 assert(terrain::imminent_capacity(bot,m)==4);assert(p.moves.size()>=2 && !p.action.child_size);strategy::remember_action(bot,m,p.action,p.moves,100);assert(m.body.size()==2);std::cout<<"Queen spends one length before chamber pearl can block its loop.\n";
#endif
}
