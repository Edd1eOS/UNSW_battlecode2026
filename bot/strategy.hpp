#pragma once
#include "helper.hpp"
#include "navigation.hpp"
#include <algorithm>
#include <deque>
#include <limits>
#include <queue>

namespace strategy {
using unswbc::Controller;
using unswbc::Direction;
using unswbc::EdgeType;
using unswbc::Position;

// 地形记忆 + 最近足迹 + 自己的身体；不把旧视野里的敌人当成现在的敌人。
struct Memory : Atlas {
    int last_split_round = -1000;
    bool role_assigned = false;
    bool reserve_worker = false;
    int splits_done = 0;
    std::deque<Position> recent;
    std::deque<Position> body; // 头到尾；可能只有已知的前半截。
    std::vector<int> traffic; // 长期访问次数，避免只记 24 步而反复绕大圈。
    void observe(const Controller& ct) {
        observe_map(ct, unswbc::game ? unswbc::game->get_round_num() : now + 1);
        if (!role_assigned) {
            // 第一批工兵繁殖一次后保留长度：Queen 若死亡，仍有第二判定的主力。
            reserve_worker = ct.get_id() > 1 && ct.get_unit_count() <= 2;
            role_assigned = true;
        }
        const Position head = ct.get_position();
        if (body.empty()) {
            body.push_back(head);
            // 初始身体按每节指向头部的方向还原；不跨未知传送门猜测。
            while (static_cast<int>(body.size()) < ct.get_length()) {
                bool added = false;
                for (const auto& tile : ct.get_tiles()) {
                    const auto* p = tile.get_dragon();
                    if (!p || p->get_id() != ct.get_id() || p->is_head()) continue;
                    if (std::find(body.begin(), body.end(), tile.get_position()) != body.end()) continue;
                    Position next;
                    if (destination(ct, tile.get_position(), p->get_dir(), next) && next == body.back()) {
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
        if (unswbc::game) {
            const auto [w, h] = unswbc::game->get_map_size();
            if (traffic.size() != static_cast<std::size_t>(w * h)) traffic.assign(w * h, 0);
            if (p.x >= 0 && p.x < w && p.y >= 0 && p.y < h)
                ++traffic[p.y * w + p.x];
        }
    }
    int visits(Position p) const {
        return static_cast<int>(std::count(recent.begin(), recent.end(), p));
    }
    int lifetime_visits(Position p) const {
        if (!unswbc::game || traffic.empty()) return 0;
        const auto [w, h] = unswbc::game->get_map_size();
        if (p.x < 0 || p.x >= w || p.y < 0 || p.y >= h) return 0;
        const auto index = static_cast<std::size_t>(p.y * w + p.x);
        return index < traffic.size() ? traffic[index] : 0;
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

// 没有普通安全步时才启用应急分裂。合法分裂可让旧尾部成为新龙头；
// 工兵可把长度交给旧尾巴；Queen 只切出最小子体，保留自己的计分长度。
// 被困头部仍可能死亡；这是最后的拖延/救援手段，不能保证主龙脱困。
// 不保证尾部安全，但避免直接输出明知会撞死的普通移动。
inline int emergency_split_size(const Controller& ct) {
    for (Direction dir : Direction::get_direction_list())
        if (ordinary_step(ct, ct.get_position(), dir)) return 0;
    bool sealed = true;
    const auto* here = ct.get_tile(ct.get_position());
    if (!here) sealed = false;
    else for (auto d : Direction::get_direction_list()) {
        const auto& edge = here->get_edge(d);
        if (edge.get_edge_type() == EdgeType::KELP) continue;
        const auto* next = ct.get_tile(ct.get_position().add_dir(d));
        const auto* part = next ? next->get_dragon() : nullptr;
        // 固定墙和不可被合法分裂移除的脖子，才能证明自己永远走不出去。
        const bool neck = edge.get_edge_type() == EdgeType::EMPTY && part
            && part->get_id() == ct.get_id() && !part->is_head()
            && next->get_edge(part->get_dir()).get_edge_type() == EdgeType::EMPTY
            && next->get_position().add_dir(part->get_dir()) == ct.get_position();
        if (!neck) sealed = false;
    }
    const int child_size = ct.get_id() <= 1 && !sealed ? 2 : ct.get_length() - 2;
    return ct.can_split(child_size) ? child_size : 0;
}

// BFS：先检查距离 0 的格子，再检查距离 1、2、3……
// 同一次搜索既统计空间，也找出最近珍珠。只搜索当前可见的格子。
inline Evaluation evaluate(const Controller& ct, Position start, const Memory* memory = nullptr) {
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
            Position target;
            if (memory) {
                if (!memory->destination(ct, tile->get_position(), dir, target)) continue;
            } else {
                if (tile->get_edge(dir).get_edge_type() != EdgeType::EMPTY) continue;
                target = tile->get_position().add_dir(dir);
            }
            const auto* next = ct.get_tile(target);
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

// 后行动的任意头部若能一步撞到我们，就扣分；同队也会撞头。
// 尚未覆盖敌人多步冲刺、未知传送门攻击；这不是完整的未来预测。
inline int nearby_threats(const Controller& ct, Position destination) {
    int threats = 0;
    for (const auto& tile : ct.get_tiles()) {
        const auto* part = tile.get_dragon();
        if (!part || !part->is_head() || part->get_id() <= ct.get_id()) continue;
        for (Direction dir : Direction::get_direction_list()) {
            if (tile.get_edge(dir).get_edge_type() == EdgeType::EMPTY
                && tile.get_position().add_dir(dir) == destination) ++threats;
        }
    }
    return threats;
}

inline int queen_crowding(const Controller& ct, Position target) {
    if (ct.get_id() <= 1 || !unswbc::game) return 0;
    const auto [w,h] = unswbc::game->get_map_size();
    for (const auto& tile : ct.get_tiles()) {
        const auto* p = tile.get_dragon();
        if (!p || !p->is_head() || p->get_id() > 1 || p->get_team() != ct.get_team()) continue;
        auto q = tile.get_position();
        int dx = std::abs(q.x-target.x), dy = std::abs(q.y-target.y);
        int distance = std::min(dx,w-dx) + std::min(dy,h-dy);
        return std::max(0, 4-distance);
    }
    return 0;
}

// v2：用小型局面副本试走。保留尾巴直到碰撞检查完成。
struct Simulation {
    std::deque<Position> body;
    std::vector<Position> eaten;
    bool complete = false;
    int length = 0;
};

inline bool simulate_step(const Controller& ct, Simulation& s, Direction dir, const Memory* memory = nullptr) {
    const auto* from = ct.get_tile(s.body.front());
    if (!from) return false;
    Position target;
    if (memory) {
        if (!memory->destination(ct, s.body.front(), dir, target)) return false;
    } else {
        if (from->get_edge(dir).get_edge_type() != EdgeType::EMPTY) return false;
        target = s.body.front().add_dir(dir);
    }
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
                                int depth, int horizon, int& budget, const Memory* memory = nullptr) {
    if (depth == horizon) return {depth, false};
    if (budget-- <= 0) return {depth, true};
    Lookahead best{depth, false};
    const auto* tile = ct.get_tile(s.body.front());
    if (!tile) return {depth, true};
    for (Direction dir : Direction::get_direction_list()) {
        Position target;
        if (memory) {
            if (!memory->destination(ct, s.body.front(), dir, target)) {
                if (tile->get_edge(dir).is_portal()) best.uncertain = true;
                continue;
            }
        } else {
            if (tile->get_edge(dir).get_edge_type() != EdgeType::EMPTY) continue;
            target = s.body.front().add_dir(dir);
        }
        if (!ct.get_tile(target)) {
            best.uncertain = true;
            continue;
        }
        Simulation next = s;
        if (!simulate_step(ct, next, dir, memory)) continue;
        Lookahead result = search_survival(ct, next, depth + 1, horizon, budget, memory);
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
    Position target;
    if (memory.destination(ct, ct.get_position(), dir, target) && !ct.get_tile(target)) return {0, true};
    if (!simulate_step(ct, state, dir, &memory)) return {0, false};
    int budget = 384;
    return search_survival(ct, state, 1, 8, budget, &memory);
}

inline Direction choose_move(const Controller& ct, const Memory& memory,
                             const std::array<double,4>& adjustment = {}) {
    const Position here = ct.get_position();
    const auto* current = ct.get_tile(here);
    Direction best = ct.get_dir();
    double best_score = -std::numeric_limits<double>::infinity();
    int best_safety = -1;
    int best_depth = -1;
    bool found = false;
    for (Direction dir : Direction::get_direction_list()) {
        Position next;
        if (!memory.destination(ct, here, dir, next)) continue;
        const auto* landing = ct.get_tile(next);
        if (landing && landing->get_dragon()) continue;
        Evaluation e = evaluate(ct, next, &memory);
        // 先重罚明显狭小的空间，再比较食物与探索收益。
        // 这是经验评分，不是“保证存活”的数学证明。
        int desired_space = std::min(ct.get_length() + 2, 20);
        double score = 2.0 * std::min(e.space, 25);
        score -= 30.0 * std::max(0, desired_space - e.space);
        if (e.exits == 0) score -= 500.0;
        score -= (ct.get_id() <= 1 ? 220.0 : 100.0) * nearby_threats(ct, next);
        score += memory.route_value(ct, next);
        score += adjustment[Atlas::direction_index(dir)];
        score -= 35.0 * queen_crowding(ct, next); // 工兵离开主龙附近，减少堵路和抢食。
        if (!landing) score -= ct.get_id() <= 1 ? 150 : 25;
        if (e.pearl_distance < 1000)
            score += 70.0 / (e.pearl_distance + 1);
        else if (e.frontier_distance < 1000)
            score += 12.0 / e.frontier_distance;
        score -= 8.0 * memory.visits(next);
        // 没看到食物时按长期足迹探索；有食物时允许重走有价值的路线。
        if (e.pearl_distance >= 1000)
            score -= 4.0 * std::min(memory.lifetime_visits(next), 30);
        if (dir == ct.get_dir()) score += 0.5;
        Lookahead future = look_ahead(ct, memory, dir);
        // v2.1：先比较退路证据，再比较食物。未知仍可选，但不能与
        // 已找到完整短期路线混为一谈。这个等级只针对简化模型。
        int safety = future.depth == 8 ? 2 : (future.uncertain ? 1 : 0);
        int depth = safety == 2 ? 8 : future.depth;
        // 无食物且已反复绕圈时，允许至少走过三步、通向未知的路线
        // 与短期已知路线竞争；仍不放宽眼前碰撞与敌头威胁。
        if ((ct.get_id() > 1 || memory.visits(here) >= 2) && e.pearl_distance >= 1000
            && safety == 1 && future.depth >= 3 && nearby_threats(ct, next) == 0) {
            safety = 2;
            depth = 8; // 仅评分待遇相同，不表示已证明八步安全。
        }
        if (!found || safety > best_safety
            || (safety == best_safety && depth > best_depth)
            || (safety == best_safety && depth == best_depth && score > best_score)) {
            found = true;
            best_safety = safety;
            best_depth = depth;
            best_score = score;
            best = dir;
        }
    }
    // 工兵在没有近处食物、明显绕圈时可以探未知门；Queen 只在无路时冒险。
    Position best_target;
    const bool best_known = memory.destination(ct, here, best, best_target);
    if (found && best_known && ct.get_id() > 1 && memory.visits(here) >= 2
        && evaluate(ct, best_target, &memory).pearl_distance >= 1000 && current) {
        for (Direction dir : Direction::get_direction_list()) {
            Position target;
            if (current->get_edge(dir).is_portal()
                && !memory.destination(ct, here, dir, target)) return dir;
        }
    }
    if (found) return best;
    // 无确认安全路时才赌未知传送门，不能拿入口旁的格子判断出口安全。
    if (current) {
        for (Direction dir : Direction::get_direction_list()) {
            Position target;
            if (current->get_edge(dir).is_portal()
                && (!memory.destination(ct, here, dir, target) || !ct.get_tile(target))) return dir;
        }
    }
    // 已无安全动作时仍输出合法指令；不能保证逃生。
    return best;
}

struct Decision {
    Direction direction;
    int child_size = 0; // 0 表示移动，否则输出 SPLIT。
};

// v4：Queen 留长度，工兵扩张。分裂本回合不移动，所以头部也要安全。
inline Decision choose_action(const Controller& ct, const Memory& memory, int round,
                              bool allow_expansion = true,
                              const std::array<double,4>& adjustment = {}) {
    Decision action{choose_move(ct, memory, adjustment), 0};
    const bool queen = ct.get_id() <= 1;
    Position target;
    const bool resolved = memory.destination(ct, ct.get_position(), action.direction, target);
    const auto* landing = resolved ? ct.get_tile(target) : nullptr;
    const bool safe_move = resolved && (!landing || !landing->get_dragon());
    const auto* current = ct.get_tile(ct.get_position());
    const bool portal_move = current && current->get_edge(action.direction).is_portal()
        && (!resolved || !landing || !landing->get_dragon());
    if (!ct.can_split(2)) return action;
    // 已知/未知传送门仍提供逃生机会，不先把 Queen 切短。
    if (!safe_move && !portal_move) {
        action.child_size = emergency_split_size(ct);
        return action;
    }
    if (static_cast<int>(memory.body.size()) != ct.get_length()) return action;
    const Position tail = memory.body.back();
    int tail_space = 0;
    for (Direction d : Direction::get_direction_list()) {
        if (!ordinary_step(ct, tail, d)) continue;
        Position p = tail.add_dir(d);
        if (nearby_threats(ct, p)) continue;
        tail_space = std::max(tail_space, evaluate(ct, p, &memory).space);
    }
    if (tail_space < 8) return action; // 尾部未知或出口拥挤，不主动分裂。
    const Lookahead future = look_ahead(ct, memory, action.direction);
    const Evaluation ahead = resolved ? evaluate(ct, target, &memory) : Evaluation{};
    // 分裂当天头不动，不能给后行动的敌头一个免费撞 Queen 的机会。
    if (nearby_threats(ct, ct.get_position()) > 0) return action;
    const bool safe_parent = future.depth >= 4;
    const int elapsed = round - memory.last_split_round;
    if (queen) {
        // 队里尚无工兵才派出一条，保留至少 8 节主龙；后期不牺牲主分数。
        if (allow_expansion && round < 160 && ct.get_length() >= 11 && ct.get_unit_count() < 2
            && elapsed >= 30 && safe_parent && tail_space >= 10) action.child_size = 3;
        return action;
    }
    // 工兵每 12 回合最多分一次；越接近终局，越重视已有长度。
    const int cap = round < 200 ? 16 : 10;
    const bool may_expand = !memory.reserve_worker || memory.splits_done == 0;
    const int split_length = memory.reserve_worker ? 12 : 8;
    if (allow_expansion && round < 350 && ct.get_length() >= split_length && ct.get_unit_count() < cap && may_expand
        && elapsed >= 12 && safe_parent && tail_space >= 10) {
        action.child_size = memory.reserve_worker ? 4 : ct.get_length() / 2;
        return action;
    }
    // 还没撞到墙，但短期模型已找不到续路；提前把长身体交给尾部。
    if (!future.uncertain && future.depth < 2 && tail_space >= 12 && ct.get_length() >= 6) {
        action.child_size = ct.get_length() - 2;
        return action;
    }
    // 无食物反复绕圈时，只有尾部空间更大才付出两节长度换方向。
    if (ct.get_length() >= 8 && memory.visits(ct.get_position()) >= 3
        && ahead.pearl_distance >= 1000 && tail_space >= ahead.space + 8) {
        action.child_size = ct.get_length() - 2;
        return action;
    }
    return action;
}

// 免费移动最多试三步：只在完整身体、当前可见路线内多走，并要求吃到珍珠。
// 不能把未知出口当成安全，也不能把上一小步吃掉的珍珠重复计算。
inline std::vector<Direction> plan_moves(const Controller& ct, const Memory& memory, Direction first) {
    std::vector<Direction> best{first};
    const int limit = std::min(3, (ct.get_length() + 3) / 4);
    if (limit < 2 || static_cast<int>(memory.body.size()) != ct.get_length()) return best;
    Simulation state{memory.body, {}, true, ct.get_length()};
    if (!simulate_step(ct, state, first, &memory)) return best;
    int best_food = static_cast<int>(state.eaten.size());
    std::vector<Direction> path{first};
    auto visit = [&](auto&& self, const Simulation& s) -> void {
        if (static_cast<int>(path.size()) >= limit) return;
        for (auto d : Direction::get_direction_list()) {
            Simulation next = s;
            if (!simulate_step(ct, next, d, &memory)) continue;
            if (nearby_threats(ct, next.body.front())) continue;
            path.push_back(d);
            int budget = 128;
            auto future = search_survival(ct, next, 0, 6, budget, &memory);
            int food = static_cast<int>(next.eaten.size());
            if (future.depth == 6 && food > best_food) { best = path; best_food = food; }
            self(self, next);
            path.pop_back();
        }
    };
    visit(visit, state);
    return best;
}

inline void remember_action(const Controller& ct, Memory& memory, const Decision& action,
                            const std::vector<Direction>& moves, int round) {
    if (action.child_size) { memory.last_split_round = round; ++memory.splits_done; return; }
    if (moves.size() <= 1) return;
    Simulation state{memory.body, {}, static_cast<int>(memory.body.size()) == ct.get_length(), ct.get_length()};
    int step = 0;
    for (auto d : moves) {
        if (!simulate_step(ct, state, d, &memory)) return;
        if (++step > (ct.get_length()+3)/4) {
            --state.length;
            if (static_cast<int>(state.body.size()) > state.length) state.body.pop_back();
        }
    }
    // 输出动作若成功，下回合应从这个身体开始；多步不能只记最后的头。
    memory.body = state.body;
}
} // namespace strategy
