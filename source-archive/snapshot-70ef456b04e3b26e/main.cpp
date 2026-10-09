#include "helper.hpp"
#include "human.hpp"
int main(){auto [ct,game]=unswbc::init();strategy::Memory memory;
while(unswbc::update(ct,game)){
 memory.observe(ct);human::Map map(ct,memory);human::AttackCache cache(ct,memory,map);
 strategy::Simulation after{memory.body,{},(int)memory.body.size()==ct.get_length(),ct.get_length()};
 if(game.get_round_num()==201)after.eaten.push_back({5,4});
 auto risk=cache.assess(after);
 std::string note="CONTRACT certain="+std::to_string(risk.certain)+" potential="+std::to_string(risk.potential)+" paths="+std::to_string(cache.path_count);
 for(const auto& e:cache.enemies)note+=" enemy="+std::to_string(e.id)+",len="+std::to_string(e.minimum)+",complete="+std::to_string(e.complete);
 ct.set_indicator_string(note);ct.make_move(unswbc::Direction::SOUTH);unswbc::end_turn();
}}
