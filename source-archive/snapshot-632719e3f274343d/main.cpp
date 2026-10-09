#include "imitation.hpp"
#include <iomanip>
int main(){auto [ct,game]=unswbc::init();strategy::Memory m;
while(unswbc::update(ct,game)){m.observe(ct);m.remember(ct.get_position());imitation::Local local(ct,m);
for(auto d:unswbc::Direction::get_direction_list()){imitation::Features f{};if(!local.features(d,f))continue;
std::cout<<"LOG FEATURE "<<strategy::Atlas::direction_index(d);for(double x:f)std::cout<<" "<<std::setprecision(10)<<x;std::cout<<"\n";}
ct.make_moves({ct.get_dir()});unswbc::end_turn();}}
