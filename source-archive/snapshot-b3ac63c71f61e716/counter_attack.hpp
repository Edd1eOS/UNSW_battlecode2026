#pragma once
#include "strategy.hpp"
#include <optional>
#include <string>
#include <unordered_map>

namespace counterplay {
struct Attack {
    std::vector<unswbc::Direction> moves;
    std::string note;
};

// Only live, visible targets are considered. Body counts are length lower
// bounds, not an estimate of a hidden tail or the opponent's longest dragon.
// A target head terminates a route; no head or body can be used as transit.
inline std::optional<Attack> attack_queen(const unswbc::Controller& ct,
                                         const strategy::Memory& memory,
                                         bool allow_ordinary = false) {
    using unswbc::Direction;
    using unswbc::Position;
    if (ct.get_id() <= 1 || ct.get_unit_count() < 3 || ct.get_length() < 2
        || !memory.cell(ct.get_position())) return std::nullopt;

    struct Target { int cell; int id; int observed; bool queen; };
    std::unordered_map<int, int> observed;
    for (const auto& tile : ct.get_tiles()) {
        const auto* part = tile.get_dragon();
        if (part && part->get_team() != ct.get_team()) ++observed[part->get_id()];
    }
    std::vector<Target> targets;
    std::vector<int> target_at(memory.cells.size(), -1);
    for (const auto& tile : ct.get_tiles()) {
        const auto* part = tile.get_dragon();
        if (!part || !part->is_head() || part->get_team() == ct.get_team()
            || !memory.cell(tile.get_position())) continue;
        const bool queen = part->get_id() <= 1;
        const int count = observed[part->get_id()];
        if (!queen && !(allow_ordinary && ct.get_length() <= 4
            && count >= ct.get_length() + (ct.get_unit_count() >= 10 ? 0 : 3))) continue;
        const int cell = memory.index(tile.get_position());
        target_at[cell] = static_cast<int>(targets.size());
        targets.push_back({cell, part->get_id(), count, queen});
    }
    if (targets.empty()) return std::nullopt;

    const int free_steps = (ct.get_length() + 3) / 4;
    // Preserve the original conservative budget: pearls never increase the
    // free allowance, and every paid step leaves at least two segments.
    const int limit = std::min(10, free_steps + ct.get_length() - 2);
    const int start = memory.index(ct.get_position());
    std::vector<int> previous(memory.cells.size(), -1), steps(memory.cells.size(), 0);
    std::vector<int> directions(memory.cells.size(), 0);
    std::queue<Position> pending;
    pending.push(ct.get_position()); previous[start] = start;
    // The official vision contains at most 49 tiles. Also bound synthetic or
    // malformed larger inputs rather than expanding over remembered terrain.
    int budget = std::min(49, static_cast<int>(ct.get_tiles().size()));
    while (!pending.empty() && budget-- > 0) {
        const auto from = pending.front(); pending.pop();
        const int at = memory.index(from);
        if (steps[at] >= limit) continue;
        for (auto dir : Direction::get_direction_list()) {
            Position to;
            if (!memory.destination(ct, from, dir, to) || !memory.cell(to)) continue;
            const int next = memory.index(to);
            if (previous[next] >= 0) continue;
            const auto* live = ct.get_tile(to);
            if (!live) continue;
            if (live->get_dragon() && target_at[next] < 0) continue;
            previous[next] = at; steps[next] = steps[at] + 1;
            directions[next] = strategy::Atlas::direction_index(dir);
            if (target_at[next] < 0) pending.push(to);
        }
    }

    const Target* best = nullptr;
    for (const auto& target : targets) {
        if (previous[target.cell] < 0) continue;
        if (!best || (target.queen && !best->queen)
            || (target.queen == best->queen && (target.observed > best->observed
                || (target.observed == best->observed &&
                    (steps[target.cell] < steps[best->cell]
                     || (steps[target.cell] == steps[best->cell] && target.id < best->id))))))
            best = &target;
    }
    if (!best) return std::nullopt;
    std::vector<Direction> path;
    for (int at = best->cell; at != start; at = previous[at])
        path.push_back(Direction::get_direction_list()[directions[at]]);
    std::reverse(path.begin(), path.end());
    return Attack{std::move(path), std::string(best->queen ? "COUNTER ATTACK_QUEEN" : "COUNTER ATTACK_LARGE_WORKER")
        + " target=" + std::to_string(best->id) + " observed=" + std::to_string(best->observed)
        + " paid=" + std::to_string(std::max(0, steps[best->cell] - free_steps))};
}
} // namespace counterplay
