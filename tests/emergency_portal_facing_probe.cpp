#include "../opponents/generalist-emergency-v1/planner.hpp"
#include <cassert>
#include <iostream>
int main(){
 auto [ct,game]=unswbc::init();assert(unswbc::update(ct,game));
 strategy::Memory memory;memory.body={{5,5},{4,5},{4,6},{8,5}};
 memory.observe_map(ct,game.get_round_num());
 const auto a=emergency::assess(ct,memory,planner::initial(ct,memory),2);
 assert(a.complete&&a.facing_known&&!a.child_no_first_move&&!a.reject);
 unswbc::Direction inferred=unswbc::Direction::NORTH;
 for(auto d:unswbc::Direction::get_direction_list()){unswbc::Position to;
  if(memory.destination(ct,a.child.body[1],d,to)&&to==a.child.body[0]){inferred=d;break;}}
 assert(inferred==unswbc::Direction::WEST);
 assert(ct.get_tile({8,5})->get_dragon()->get_dir()==unswbc::Direction::EAST);
 std::cout<<"{\"inferred_child_facing\":\""<<inferred.value<<"\",\"old_tail_part_direction\":\"E\",\"reject\":false}\n";
}
