#pragma once
#include "strategy.hpp"

namespace counterplay {
using namespace strategy;

// 只标记本回合还未行动的可见龙头的一步落点。它是冲撞可能性，
// 不是对手必走这一步的预测，也不是更长冲刺的安全上界。
struct Endpoints {
    std::vector<int> enemies, allies;
    bool contested(const Memory& m, Position p) const {
        if(!m.cell(p)) return false;
        const auto i=m.index(p);
        return enemies[i]>0 || allies[i]>0;
    }
};

inline Endpoints endpoints(const Controller& ct, const Memory& m) {
    Endpoints result;
    result.enemies.assign(m.cells.size(),0);
    result.allies.assign(m.cells.size(),0);
    for(const auto& tile:ct.get_tiles()) {
        const auto* part=tile.get_dragon();
        if(!part || !part->is_head() || part->get_id()<=ct.get_id()) continue;
        for(auto d:Direction::get_direction_list()) {
            Position out;
            if(!m.destination(ct,tile.get_position(),d,out) || !m.cell(out)) continue;
            const auto* live=ct.get_tile(out);
            if(!live) continue;
            const auto* body=live->get_dragon();
            // 自己的旧身体可能随本次动作腾开；其他当前身体仍挡住对手。
            if(body && body->get_id()!=ct.get_id()) continue;
            auto& count=part->get_team()==ct.get_team()?result.allies:result.enemies;
            ++count[m.index(out)];
        }
    }
    return result;
}

// 有至少两步续路时，优先留在没有即时抢头风险的落点。
// 若所有替代路线都已确认很快封死，仍保留冒险逃生选项。
inline int continuation_class(const Lookahead& future, bool contested) {
    if(future.depth<2 && !future.uncertain) return 0;
    return contested?1:2;
}
}
