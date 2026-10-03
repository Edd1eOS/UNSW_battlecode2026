#include "../opponents/v54-queen-buffer-escape/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
    Game board{15,15,64}; game=&board;
    Controller queen{0,Team::A,Direction::EAST,Vision{},64};ct=&queen;
    std::vector<Tile> tiles;
    for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
        tiles.emplace_back(Position{x,y},std::nullopt,-1);
    queen.vision=Vision{std::move(tiles)};queen.head.position={5,5};
    queen.length=4;queen.unit_count=4;
    strategy::Memory memory;memory.body={{5,5},{4,5},{3,5},{2,5}};
    queen.get_tile({5,5})->dragon_part=queen.head;
    for(int i=1;i<4;++i) queen.get_tile(memory.body[i])->dragon_part=
        DragonPart{memory.body[i],0,Team::A,Direction::EAST,false};
    auto enemy=[&](int id,Position head,Position tail,Direction dir) {
        queen.get_tile(head)->dragon_part=DragonPart{head,id,Team::B,dir,true};
        queen.get_tile(tail)->dragon_part=DragonPart{tail,id,Team::B,dir,false};
    };
    enemy(3,{5,3},{6,3},Direction::WEST);
    enemy(5,{7,5},{7,4},Direction::SOUTH);
    enemy(7,{5,7},{4,7},Direction::EAST);
    memory.observe_map(queen,40);
    assert(forage::enemy_reach(queen,memory,*queen.get_tile({5,3}))==1);
    auto danger=forage::queen_danger(queen,memory);
    assert(danger[memory.index({5,4})]>=1);
    assert(danger[memory.index({6,5})]>=1);
    assert(danger[memory.index({5,6})]>=1);
    forage::State state;auto plan=forage::choose(queen,memory,state);
    assert(plan.moves.size()>=2 && plan.action.child_size==0);
    strategy::remember_action(queen,memory,plan.action,plan.moves,40);
    assert(danger[memory.index(memory.body.front())]==0);
    assert(memory.body.size()==4-(plan.moves.size()-1));
    std::cout << "Queen leaves a three-sided one-step attack using paid escape; body memory matches cost.\n";
}
