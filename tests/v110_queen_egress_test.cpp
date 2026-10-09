#include "../opponents/v110-queen-egress/forage.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64}; Controller bot{2,Team::A,Direction::WEST,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game=&board;ct=&bot;board.round_num=100;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={6,6};bot.length=3;bot.unit_count=5;
        memory.body={{6,6},{7,6},{8,6}};
        for(int i=0;i<3;++i)bot.get_tile(memory.body[i])->dragon_part=DragonPart{memory.body[i],2,Team::A,Direction::WEST,i==0};
        bot.get_tile({5,4})->dragon_part=DragonPart{{5,4},0,Team::A,Direction::SOUTH,true};
        bot.get_tile({5,3})->dragon_part=DragonPart{{5,3},0,Team::A,Direction::SOUTH,false};
        wall({5,4},Direction::WEST);wall({5,4},Direction::SOUTH);
        memory.observe_map(bot,100);
    }
    void wall(Position p,Direction d) {bot.get_tile(p)->get_edge(d).edge_type=EdgeType::KELP;bot.get_tile(p.add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;}
};
int main() {
    Scene s;queen_egress::Guard guard(s.bot,s.memory);assert(guard.active && guard.before==1);
    strategy::Simulation closes{{{7,4},{6,4},{6,5}},{},true,3};
    strategy::Simulation clear{{{7,5},{6,5},{6,6}},{},true,3};
    assert(guard.count(&closes)==0 && guard.damage(closes)==1);
    assert(guard.count(&clear)==1 && guard.damage(clear)==0);
    // The head is away from the exit in both candidates: all body segments matter.
    assert(closes.body.front()!=Position(6,4));
    s.bot.get_tile({5,4})->dragon_part->team=Team::B;
    queen_egress::Guard enemy(s.bot,s.memory);assert(!enemy.active && enemy.damage(closes)==0);
    s.bot.get_tile({5,4})->dragon_part->team=Team::A;
    s.bot.head.dragon_id=0;queen_egress::Guard queen(s.bot,s.memory);assert(!queen.active);
    std::cout<<"Visible allied Queen's final exit accounts for whole worker body; enemy and Queen callers excluded.\n";
}

