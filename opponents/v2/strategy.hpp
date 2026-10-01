#pragma once
#include "helper.hpp"
#include <algorithm>
#include <deque>
#include <limits>
#include <queue>

namespace strategy {
using unswbc::Controller;
using unswbc::Direction;
using unswbc::EdgeType;
using unswbc::Position;

// 只记最近走过的位置，不把旧视野里的敌人当成现在的敌人。
struct Memory {
    std::deque<Position> recent;
    std::deque<Position> body; // 头到尾；可能只有已知的前半截。
    void observe(const Controller& ct) {
        const Position head = ct.get_position();
        if (body.empty()) {
            body.push_back(head);
            // 初始身体按每节指向头部的方向还原；不跨未知传送门猜测。
            while (static_cast<int>(body.size()) < ct.get_length()) {
                bool added = false;
                for (const auto& tile : ct.get_tiles()) {
                    const auto* p = tile.get_dragon();
                    if (!p || p->get_id() != ct.get_id() || p->is_head()) continue;
                    if (tile.get_edge(p->get_dir()).get_edge_type() != EdgeType::EMPTY) continue;
                    if (std::find(body.begin(), body.end(), tile.get_position()) != body.end()) continue;
                    if (tile.get_position().add_dir(p->get_dir()) == body.back()) {
                        body.push_back(tile.get_position()); added = true; break;
                    }
                }
                if (!added) break;
            }
        } else if (body.front() != head) {
            body.push_front(head);
        }
        while (static_cast<int>(body.size()) > ct.get_length()) body.pop_back();
    }
    void remember(Position p) {
        recent.push_back(p);
        if (recent.size() > 24) recent.pop_front();
    }
    int visits(Position p) const {
        return static_cast<int>(std::count(recent.begin(), recent.end(), p));
    }
};

struct Evaluation {
    int space = 0;
    int pearl_distance = 1000;
    int exits = 0;
    int frontier_distance = 1000;
};

// 普通边才按相邻格子处理。传送门的出口不是相邻格子。
inline bool ordinary_step(const Controller& ct, Position from, Direction dir) {
    const auto* tile = ct.get_tile(from);
    if (!tile || tile->get_edge(dir).get_edge_type() != EdgeType::EMPTY)
        return false;
    const auto* next = ct.get_tile(from.add_dir(dir));
    return next && !next->get_dragon();
}

// BFS：先检查距离 0 的格子，再检查距离 1、2、3……
// 同一次搜索既统计空间，也找出最近珍珠。只搜索当前可见的格子。
inline Evaluation evaluate(const Controller& ct, Position start) {
    Evaluation result;
    const auto& tiles = ct.get_tiles();
    std::vector<int> distance(tiles.size(), -1);
    std::queue<const unswbc::Tile*> pending;
    const auto* first = ct.get_tile(start);
    if (!first || first->get_dragon()) return result;
    distance[first - tiles.data()] = 0;
    pending.push(first);
    while (!pending.empty()) {
        const auto* tile = pending.front();
        pending.pop();
        const int depth = distance[tile - tiles.data()];
        ++result.space;
        if (tile->has_pearl())
            result.pearl_distance = std::min(result.pearl_distance, depth);
        for (Direction dir : Direction::get_direction_list()) {
            if (tile->get_edge(dir).get_edge_type() != EdgeType::EMPTY) continue;
            const auto* next = ct.get_tile(tile->get_position().add_dir(dir));
            if (!next) {
                // 视野之外只是未知，不计为已确认的安全空间。
                result.frontier_distance = std::min(result.frontier_distance, depth + 1);
                continue;
            }
            if (next->get_dragon()) continue;
            if (depth == 0) ++result.exits;
            auto index = next - tiles.data();
            if (distance[index] != -1) continue;
            distance[index] = depth + 1;
            pending.push(next);
        }
    }
    return result;
}

// 后行动的敌方头部若能一步撞到我们，就扣分；这不是完整的敌方预测。
inline int nearby_threats(const Controller& ct, Position destination) {
    int threats = 0;
    for (const auto& tile : ct.get_tiles()) {
        const auto* part = tile.get_dragon();
        if (!part || !part->is_head() || part->get_team() == ct.get_team()
            || part->get_id() <= ct.get_id()) continue;
        for (Direction dir : Direction::get_direction_list()) {
            if (tile.get_edge(dir).get_edge_type() == EdgeType::EMPTY
                && tile.get_position().add_dir(dir) == destination) ++threats;
        }
    }
    return threats;
}

// v2：用小型局面副本试走。保留尾巴直到碰撞检查完成。
struct Simulation {
    std::deque<Position> body;
    std::vector<Position> eaten;
    bool complete = false;
    int length = 0;
};

inline bool simulate_step(const Controller& ct, Simulation& s, Direction dir) {
    const auto* from = ct.get_tile(s.body.front());
    if (!from || from->get_edge(dir).get_edge_type() != EdgeType::EMPTY) return false;
    Position target = s.body.front().add_dir(dir);
    const auto* tile = ct.get_tile(target);
    if (!tile) return false; // 未知区域交给搜索函数单独标记。
    if (std::find(s.body.begin(), s.body.end(), target) != s.body.end()) return false;
    const auto* part = tile->get_dragon();
    if (part && (part->get_id() != ct.get_id() || !s.complete)) return false;
    bool grows = tile->has_pearl()
        && std::find(s.eaten.begin(), s.eaten.end(), target) == s.eaten.end();
    s.body.push_front(target);
    if (grows) { s.eaten.push_back(target); ++s.length; }
    if (static_cast<int>(s.body.size()) > s.length) s.body.pop_back();
    return true;
}

struct Lookahead {
    int depth = 0;
    bool uncertain = false;
};

// 深度优先试走：找到一条能走满 horizon 的路线即可，不穷举所有路线。
// 节点上限控制计算量；搜索耗尽和未知区域都不能当作“确认必死”。
inline Lookahead search_survival(const Controller& ct, const Simulation& s,
                                int depth, int horizon, int& budget) {
    if (depth == horizon) return {depth, false};
    if (budget-- <= 0) return {depth, true};
    Lookahead best{depth, false};
    const auto* tile = ct.get_tile(s.body.front());
    if (!tile) return {depth, true};
    for (Direction dir : Direction::get_direction_list()) {
        if (tile->get_edge(dir).get_edge_type() != EdgeType::EMPTY) continue;
        if (!ct.get_tile(s.body.front().add_dir(dir))) {
            best.uncertain = true;
            continue;
        }
        Simulation next = s;
        if (!simulate_step(ct, next, dir)) continue;
        Lookahead result = search_survival(ct, next, depth + 1, horizon, budget);
        best.depth = std::max(best.depth, result.depth);
        best.uncertain = best.uncertain || result.uncertain;
        if (best.depth == horizon) return best;
    }
    return best;
}

inline Lookahead look_ahead(const Controller& ct, const Memory& memory, Direction dir) {
    Simulation state;
    state.body = memory.body;
    if (state.body.empty()) state.body.push_back(ct.get_position());
    state.complete = static_cast<int>(state.body.size()) == ct.get_length();
    state.length = ct.get_length();
    if (!simulate_step(ct, state, dir)) return {0, false};
    int budget = 384;
    return search_survival(ct, state, 1, 8, budget);
}

inline Direction choose_move(const Controller& ct, const Memory& memory) {
    const Position here = ct.get_position();
    const auto* current = ct.get_tile(here);
    Direction best = ct.get_dir();
    double best_score = -std::numeric_limits<double>::infinity();
    bool found = false;
    for (Direction dir : Direction::get_direction_list()) {
        if (!ordinary_step(ct, here, dir)) continue;
        Position next = here.add_dir(dir);
        Evaluation e = evaluate(ct, next);
        // 先重罚明显狭小的空间，再比较食物与探索收益。
        // 这是经验评分，不是“保证存活”的数学证明。
        int desired_space = std::min(ct.get_length() + 2, 20);
        double score = 2.0 * std::min(e.space, 25);
        score -= 30.0 * std::max(0, desired_space - e.space);
        if (e.exits == 0) score -= 500.0;
        score -= 80.0 * nearby_threats(ct, next);
        if (e.pearl_distance < 1000)
            score += 70.0 / (e.pearl_distance + 1);
        else if (e.frontier_distance < 1000)
            score += 12.0 / e.frontier_distance;
        score -= 8.0 * memory.visits(next);
        if (dir == ct.get_dir()) score += 0.5;
        Lookahead future = look_ahead(ct, memory, dir);
        // 只重罚在当前简化模型里找不到退路的方向；未知不等于死亡。
        if (!future.uncertain && future.depth < 8)
            score -= 1000.0 * (8 - future.depth);
        if (!found || score > best_score) {
            found = true;
            best_score = score;
            best = dir;
        }
    }
    if (found) return best;
    // 普通路全被堵住时才赌传送门，不能拿入口旁的格子判断出口安全。
    if (current) {
        for (Direction dir : Direction::get_direction_list())
            if (current->get_edge(dir).is_portal()) return dir;
    }
    // 已无安全动作时仍输出合法指令；不能保证逃生。
    return best;
}
} // namespace strategy
