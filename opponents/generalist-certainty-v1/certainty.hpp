#pragma once
// Called only after equal contact, continuation grade and birth-contact tier.
// Known and finite routes retain their original utility ordering. Unknown
// depth is already observed/search evidence, never a guarantee of survival.
namespace certainty {
inline int comparable_unknown_depth(bool protect,int grade,int depth) {
    return protect && grade==2 ? depth : 0;
}
inline bool prefer_after_birth(bool protect,int grade,int depth,double utility,
                               int incumbent_depth,double incumbent_utility) {
    const int a=comparable_unknown_depth(protect,grade,depth);
    const int b=comparable_unknown_depth(protect,grade,incumbent_depth);
    return a>b || (a==b && utility>incumbent_utility);
}
}
