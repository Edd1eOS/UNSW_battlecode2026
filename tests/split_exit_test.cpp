#include "../opponents/v55-colony-adaptive/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
 Game board{15,15,64};game=&board;
 Controller queen{0,Team::A,Direction::EAST,Vision{},64};ct=&queen;
 std::vector<Tile> tiles;
 for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y},std::nullopt,-1);
 queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};queen.length=4;queen.unit_count=4;
 strategy::Memory memory;memory.body={{5,5},{4,5},{3,5},{2,5}};
 for(int i=0;i<4;++i) queen.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],0,Team::A,Direction::EAST,i==0};
 memory.observe_map(queen,0);
 assert(forage::split_has_exit(queen,memory,2));
 forage::State state;assert(forage::choose(queen,memory,state).action.child_size==2);
 auto* tail=queen.get_tile({2,5});
 for(auto d:{Direction(Direction::NORTH),Direction(Direction::SOUTH),Direction(Direction::WEST)})
  tail->edges[strategy::Atlas::direction_index(d)].edge_type=EdgeType::KELP;
 memory.observe_map(queen,0);
 assert(!forage::split_has_exit(queen,memory,2));
 assert(forage::choose(queen,memory,state).action.child_size==0);
 std::cout<<"Founder expands in open space but does not create a child sealed behind its neck.\n";
}
