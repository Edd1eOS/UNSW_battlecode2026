// Regression: remembered remote source is unresolved for the current simulator.
#include "../opponents/generalist-emergency-v2/emergency.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
int main() {
 Game board{20,20,64};Controller actor{2,Team::A,Direction::NORTH,Vision{},64};
 game=&board;ct=&actor;actor.head.position={5,5};actor.length=7;actor.unit_count=3;
 std::vector<Tile> tiles;
 for(int y=2;y<=8;++y)for(int x=2;x<=8;++x){
  tiles.emplace_back(Position{x,y},std::nullopt,-1);
  for(auto d:Direction::get_direction_list())tiles.back().get_edge(d)=Edge{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::KELP,-1};
 }
 actor.vision=Vision{std::move(tiles)};
 strategy::Memory m;
 m.body={{5,5},{5,6},{6,6},{7,6},{8,6},{9,6},{9,5}};
 for(int i=0;i<(int)m.body.size();++i)if(auto* t=actor.get_tile(m.body[i]))
  t->dragon_part=DragonPart{m.body[i],2,Team::A,Direction::NORTH,i==0};
 actor.get_tile({8,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::EMPTY,-1};
 m.observe_map(actor,20);
 // A possible historical observation remembers the remote birth head/neck.
 for(auto p:std::vector<Position>{{9,5},{9,6}}){
  auto& cell=m.cells[m.index(p)];cell.known=true;
  for(auto d:Direction::get_direction_list())cell.edges[strategy::Atlas::direction_index(d)]=Edge{d==Direction(Direction::NORTH)||d==Direction::SOUTH,EdgeType::KELP,-1};
 }
 m.cells[m.index({9,6})].edges[strategy::Atlas::direction_index(Direction::NORTH)]=Edge{true,EdgeType::EMPTY,-1};
 m.cells[m.index({9,5})].edges[strategy::Atlas::direction_index(Direction::SOUTH)]=Edge{true,EdgeType::EMPTY,-1};
 m.cells[m.index({9,5})].edges[strategy::Atlas::direction_index(Direction::WEST)]=Edge{false,EdgeType::EMPTY,-1};
 strategy::Simulation original{m.body,{},true,7};auto a=emergency::assess(actor,m,original,2);
 assert(a.complete&&a.facing_known&&!a.child_no_first_move&&a.child_future.unknown&&!a.reject);
 assert(!actor.get_tile(a.child.body.front()));
 Position destination;assert(m.destination(actor,a.child.body.front(),Direction::WEST,destination));
 assert(destination==Position(8,5)&&actor.get_tile(destination)&&!actor.get_tile(destination)->get_dragon());
 assert(!emergency::has(a.child.body,destination)&&!emergency::has(a.parent.body,destination));
 // Legal current destination exists, but the inherited simulator rejects
 // solely because its source tile is outside the current actor's window.
 auto child=a.child;assert(!strategy::simulate_step(actor,child,Direction::WEST,&m));
 std::cout<<"PASS diagnostic: legal remote-head W into visible free square stays unknown instead of false child_no_first_move\n";
}
