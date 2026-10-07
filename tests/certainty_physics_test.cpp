#include "../opponents/generalist-certainty-v1/planner.hpp"
#include <cassert>
#include <iostream>

int main() {
    using certainty::prefer_after_birth;
    using certainty::comparable_unknown_depth;
    // Protected unknown candidates: six confirmed steps beat zero even
    // when the old food utility strongly prefers zero. The reverse loses.
    assert(prefer_after_birth(true,2,6,-100,0,10000));
    assert(!prefer_after_birth(true,2,0,10000,6,-100));
    // Same evidence preserves the exact strict old utility/tie behavior.
    assert(prefer_after_birth(true,2,6,2,6,1));
    assert(!prefer_after_birth(true,2,6,1,6,1));
    // Ordinary workers, complete horizon and known finite continuation
    // retain old utility ordering; no new grade or depth is invented.
    assert(prefer_after_birth(false,2,0,100,6,0));
    assert(!prefer_after_birth(false,2,6,0,0,100));
    for(int grade : {0,1,3}) {
        assert(comparable_unknown_depth(true,grade,6)==0);
        assert(prefer_after_birth(true,grade,0,100,6,0));
        assert(!prefer_after_birth(true,grade,6,0,0,100));
    }
    // Search exhaustion is evidence grade2 at its actual completed depth.
    // It is neither promoted to a horizon nor merged with grade3.
    planner::Future exhausted{4,false,false,true};
    assert(planner::future_grade(exhausted,8)==2);
    assert(comparable_unknown_depth(true,2,exhausted.depth)==4);
    assert(prefer_after_birth(true,2,4,0,0,100));
    planner::Future finite{3,false,false,false};
    planner::Future known{8,false,false,false};
    assert(planner::future_grade(finite,8)==1);
    assert(planner::future_grade(known,8)==3);
    assert(comparable_unknown_depth(true,1,finite.depth)==0);
    assert(comparable_unknown_depth(true,3,known.depth)==0);
    // This is the existing higher-level contact order, which still runs
    // before this helper. Future/birth ordering is unchanged in choose.
    planner::Candidate direct;
    direct.imminent=true;
    assert(planner::contact_tier(direct,true,3)==0);
    direct.imminent=false;
    assert(planner::contact_tier(direct,true,2)==1);
    std::cout << "certainty unknown0vs6/equal/worker/known/finite/exhausted PASS\n";
}
