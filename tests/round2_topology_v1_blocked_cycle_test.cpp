#include "../opponents/generalist-topology-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};Controller bot{0,Team::A,Direction::NORTH,Vision{},64};
    strategy::Memory m;planner::State state;
    Scene(){game=&board;ct=&bot;bot.head.position={5,5};bot.length=2;bot.unit_count=2;
        std::vector<Tile> tiles;for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){
            Tile t(Position{x,y},std::nullopt,-1);for(auto d:Direction::get_direction_list())t.get_edge(d)=Edge{false,EdgeType::KELP,-1};tiles.push_back(t);}
        bot.vision=Vision{std::move(tiles)};m.body={{5,5},{5,6}};
        bot.get_tile({5,5})->dragon_part=bot.head;
        bot.get_tile({5,6})->dragon_part=DragonPart{{5,6},0,Team::A,Direction::NORTH,false};
        path({{5,6},{5,5},{5,4},{5,3},{6,3},{7,3},{7,4},{7,5},{7,6},{6,6},{6,7},{5,7}});
        path({{5,5},{4,5},{3,5},{3,4},{3,3},{4,3},{4,4},{4,5}});
        bot.get_tile({5,4})->pearl=true;bot.get_tile({5,3})->pearl=true;m.observe_map(bot,100);}
    void path(std::initializer_list<Position> points){auto a=points.begin();auto b=a;++b;for(;b!=points.end();++a,++b){
        bool found=false;for(auto d:Direction::get_direction_list())if(a->add_dir(d)==*b){
            bot.get_tile(*a)->get_edge(d)=Edge{};bot.get_tile(*b)->get_edge(d.get_opposite())=Edge{};found=true;break;}assert(found);}}
};
int main(){Scene s;s.bot.get_tile({3,4})->dragon_part=DragonPart{{3,4},9,Team::B,Direction::NORTH,false};
 auto p=planner::choose(s.bot,s.m,s.state);assert(p.moves.front()==Direction(Direction::WEST));}
