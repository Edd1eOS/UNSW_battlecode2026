#ifdef CURRENT_BOT
#include "../bot/forage.hpp"
#elif defined(OLD_BASELINE)
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#else
#include "../opponents/v95-scout-body-check/forage.hpp"
#endif
#include <cassert>
#include <iostream>
int main(){auto [ct,g]=unswbc::init();strategy::Memory m;forage::State s;while(unswbc::update(ct,g)){m.observe(ct);m.remember(ct.get_position());if(g.get_round_num()!=107) continue;unswbc::Position out;assert(m.destination(ct,ct.get_position(),unswbc::Direction::EAST,out));assert(!ct.get_tile(out));assert(std::find(m.body.begin(),m.body.end(),out)!=m.body.end());auto p=forage::choose(ct,m,s);
#ifdef OLD_BASELINE
assert(p.moves.size()==1 && p.moves[0]==unswbc::Direction(unswbc::Direction::EAST));std::cout<<"Baseline portal scout returns into its own hidden body.\n";
#else
assert(p.moves.empty() || p.moves[0]!=unswbc::Direction(unswbc::Direction::EAST));std::cout<<"Known portal exit occupied by remembered own body is rejected.\n";
#endif
return 0;}}
