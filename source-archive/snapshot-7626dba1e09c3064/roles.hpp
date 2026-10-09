#pragma once
#include "strategy.hpp"

// Regional election uses only currently visible worker heads and a verified
// visible-chain length lower bound. It cannot identify a global champion.
namespace regional_role {
struct State { bool founder=false,champion=false;int visible_winner=-1; };
template<class ObservedLength>
inline bool update(const unswbc::Controller& ct,const strategy::Memory& memory,State& state,
                   ObservedLength observed_length) {
    if(ct.get_id()<=1)return false;
    state.founder=state.founder||(memory.reserve_worker&&memory.splits_done>=1);
    state.visible_winner=-1;
    for(const auto& tile:ct.get_tiles()) {
        const auto* p=tile.get_dragon();
        if(!p||!p->is_head()||p->get_team()!=ct.get_team()||p->get_id()<=1||p->get_id()==ct.get_id())continue;
        const int lower=observed_length(p->get_id());
        // A lower bound can prove another worker is at least as long. Missing
        // tail/body cannot prove it is shorter than us.
        if(lower>=8&&(lower>ct.get_length()||(lower==ct.get_length()&&p->get_id()<ct.get_id())))
            state.visible_winner=p->get_id();
    }
    if(state.visible_winner>=0)state.champion=false;
    else if(ct.get_length()>=8)state.champion=true;
    return state.founder||state.champion;
}
} // namespace regional_role
