#include "../opponents/generalist-foraging-v1/planner.hpp"
#include <cassert>
#include <cstdlib>
#include <iostream>
using namespace unswbc;
int main(int argc,char** argv) {
 const int length=argc>1?std::atoi(argv[1]):3;
 const bool portals=argc>2&&std::atoi(argv[2]);
 const int identity=argc>3?std::atoi(argv[3]):2;
 assert(length==3||length==32);
 Game board{64,64,64};Controller bot{identity,Team::A,Direction::EAST,Vision{},64};
 game=&board;ct=&bot;bot.head.position={32,32};bot.length=length;bot.unit_count=10;
 strategy::Memory memory;memory.width=64;memory.height=64;memory.now=200;
 memory.cells.assign(4096,{});
 for(auto& c:memory.cells){c.known=true;c.seen=1;}
 // A possible historical terrain cache, not a claim that a particular
 // production dragon really observed this route. All ordinary body links
 // remain empty; portal mouths are symmetric and globally consistent.
 if(portals)for(int k=0;k<12;++k) {
  Position a{(k*5+3)%64,(k*7+4)%64},b{(k*11+33)%64,(k*13+40)%64};
  // Keep the complete current ordinary body row unobstructed.
  if(a.y==32||b.y==32)continue;
  const int id=100+k;
  for(auto p:{a,b}) {
   memory.cells[memory.index(p)].edges[1]=Edge{false,EdgeType::PORTAL,id};
   memory.cells[memory.index(p.add_dir(Direction::EAST))].edges[3]=Edge{false,EdgeType::PORTAL,id};
  }
  memory.portals[id]={{a,false},{b,false}};
 }
 for(int i=0;i<length;++i)memory.body.push_back({32-i,32});
 std::vector<Tile> tiles;int pearls=0;
 for(int y=29;y<=35;++y)for(int x=29;x<=35;++x) {
  Position p{x,y};tiles.emplace_back(p,std::nullopt,-1);tiles.back().edges=memory.cells[memory.index(p)].edges;
  if(std::find(memory.body.begin(),memory.body.end(),p)==memory.body.end()&&pearls<16) {
   tiles.back().pearl=true;++pearls;
  }
 }
 bot.vision=Vision{std::move(tiles)};
 for(int i=0;i<length;++i)if(auto* t=bot.get_tile(memory.body[i]))
  t->dragon_part=DragonPart{memory.body[i],identity,Team::A,Direction::EAST,i==0};
 memory.observe_map(bot,200);assert(bot.get_tiles().size()==49&&pearls==16);
 const auto field=foraging::build(bot,memory);assert(field.sources.size()==16);
 planner::State state;const auto plan=planner::choose(bot,memory,state);
 assert(plan.action.child_size>0||!plan.moves.empty());
 std::cout<<"{\"length\":"<<length<<",\"portals\":"<<portals<<",\"identity\":"<<identity
  <<",\"sources\":"<<field.sources.size()<<",\"work\":"<<field.work
  <<",\"exhausted\":"<<field.exhausted<<",\"action\":\"";
 if(plan.action.child_size>0)std::cout<<"SPLIT "<<plan.action.child_size;
 else {std::cout<<"MOVE ";for(auto d:plan.moves)std::cout<<d.value;}
 std::cout<<"\"}\n";
}
