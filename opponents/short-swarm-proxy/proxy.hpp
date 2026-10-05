#pragma once
#include "forage.hpp"

// A behavioral test proxy, not a reconstruction of any opponent's source.
namespace short_swarm_proxy {
using namespace strategy;

inline bool tail_has_visible_exit(const Controller& ct, const Memory& m) {
    if (static_cast<int>(m.body.size()) != ct.get_length()) return false;
    const auto* tail = ct.get_tile(m.body.back());
    if (!tail) return false;
    for (auto d : Direction::get_direction_list()) {
        if (tail->get_edge(d).get_edge_type() != EdgeType::EMPTY) continue;
        const auto* out = ct.get_tile(tail->get_position().add_dir(d));
        if (out && !out->get_dragon()) return true;
    }
    return false;
}

// Only ordinary adjacent edges are eligible. A remembered portal is not an
// adjacent attack, and neither old enemy positions nor sonar are consulted.
inline std::vector<Direction> adjacent_attack(const Controller& ct) {
    const auto* here = ct.get_tile(ct.get_position());
    if (!here) return {};
    int best = -1;
    std::vector<Direction> attack;
    for (auto d : Direction::get_direction_list()) {
        if (here->get_edge(d).get_edge_type() != EdgeType::EMPTY) continue;
        const auto* out = ct.get_tile(ct.get_position().add_dir(d));
        const auto* p = out ? out->get_dragon() : nullptr;
        if (!p || !p->is_head() || p->get_team() == ct.get_team()) continue;
        const int value = p->get_id() <= 1 ? 2 : 1;
        if (value > best) { best = value; attack = {d}; }
    }
    return attack;
}

// Routes remain inside this turn's vision. Current visible pearls are strongest,
// visible countdowns <=12 are weaker, then an as-yet-unseen frontier. Terrain
// memory is used only to identify known portal exits and unseen frontier cells.
inline double resource_value(const Controller& ct, const Memory& m, Position start) {
    std::vector<int> distance(m.cells.size(), -1);
    std::queue<Position> q;
    q.push(start); distance[m.index(start)] = 0;
    double best = 0;
    while (!q.empty()) {
        const auto p = q.front(); q.pop();
        const auto* tile = ct.get_tile(p);
        if (!tile) continue;
        const int depth = distance[m.index(p)];
        if (tile->has_pearl()) best = std::max(best, 100.0 / (depth + 1));
        const int countdown = tile->get_pearl_time();
        if (!tile->has_pearl() && countdown >= 0 && countdown <= 12)
            best = std::max(best, 24.0 / (depth + countdown + 2));
        for (auto d : Direction::get_direction_list()) {
            Position n;
            if (!m.destination(ct, p, d, n) || !m.cell(n)) continue;
            const auto* next = ct.get_tile(n);
            if (!next) {
                if (!m.cell(n)->known) best = std::max(best, 10.0 / (depth + 1));
                continue;
            }
            if (next->get_dragon() || distance[m.index(n)] >= 0) continue;
            distance[m.index(n)] = depth + 1; q.push(n);
        }
    }
    return best;
}

inline forage::Plan choose(const Controller& ct, Memory& m, forage::State& state) {
    // Queen exactly retains frozen v66's policy, including its existing limits.
    if (ct.get_id() <= 1) return forage::choose(ct, m, state);
    const auto attack = adjacent_attack(ct);
    if (!attack.empty()) return {{attack.front(), 0}, attack, "PROXY SHORT ADJACENT_ATTACK"};
    if (ct.can_split(2) && tail_has_visible_exit(ct, m))
        return {{ct.get_dir(), 2}, {}, "PROXY SHORT SPLIT2"};

    Direction best = ct.get_dir();
    double best_score = -std::numeric_limits<double>::infinity();
    bool found = false;
    for (auto d : Direction::get_direction_list()) {
        Simulation next{m.body, {}, static_cast<int>(m.body.size()) == ct.get_length(), ct.get_length()};
        if (next.body.empty()) next.body.push_back(ct.get_position());
        if (!simulate_step(ct, next, d, &m)) continue;
        const auto end = next.body.front();
        double score = resource_value(ct, m, end);
        score -= 3.0 * m.visits(end) + 0.5 * std::min(m.lifetime_visits(end), 20);
        if (d == ct.get_dir()) score += 0.1;
        if (!found || score > best_score) { found = true; best_score = score; best = d; }
    }
    // When every visible destination is occupied/blocked, probe a real portal
    // rather than pretending that its geometrically adjacent tile is the exit.
    if (!found) {
        const auto* here = ct.get_tile(ct.get_position());
        if (here) for (auto d : Direction::get_direction_list()) {
            if (here->get_edge(d).is_portal()) { best = d; break; }
        }
    }
    // One step is free at every legal length under the Oct1 ceil(length/4) rule.
    return {{best, 0}, {best}, "PROXY SHORT ONE_STEP"};
}
} // namespace short_swarm_proxy
