#include "../bot/forage.hpp"
#include <cassert>
// Feed observations from a real recorded trajectory. Before the target snapshot,
// no candidate decisions are executed; memory records observed positions only.
int main() {
 auto [ct,game]=unswbc::init();strategy::Memory memory;forage::State state;
 while(unswbc::update(ct,game)) {
  memory.observe(ct);memory.remember(ct.get_position());
  if(game.get_round_num()!=18) continue;
  auto plan=forage::choose(ct,memory,state);
  assert(plan.moves.size()==1 && plan.moves[0]==unswbc::Direction(unswbc::Direction::WEST));
  assert(plan.note.find("PORTAL_SCOUT")!=std::string::npos);
  std::cout<<"Snapshot 18: known portal selected toward remembered pearl.\n";
 }
}
