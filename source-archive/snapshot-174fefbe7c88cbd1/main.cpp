#include "helper.hpp"
#include "human.hpp"
int main(){auto [ct,game]=unswbc::init();strategy::Memory memory;
while(unswbc::update(ct,game)){memory.observe(ct);
 strategy::Simulation after{memory.body,{},(int)memory.body.size()==ct.get_length(),ct.get_length()};
 int budget=256;auto route=human::terrain_continuation(ct,memory,after,0,8,budget);
 ct.set_indicator_string("TERRAIN depth="+std::to_string(route.depth)+" uncertain="+std::to_string(route.uncertain)+" outside="+std::to_string(route.outside)+" nodes="+std::to_string(256-budget));
 ct.make_move(unswbc::Direction::SOUTH);unswbc::end_turn();}}
