#pragma once
#include "strategy.hpp"
#include <unordered_map>

// Resource competition from this dragon's current window only. These are
// free-move opportunities on a static visible graph, not predicted enemy
// actions, exact enemy lengths, upper reach bounds, or a safety test.
namespace contest {
using unswbc::Controller;
using unswbc::Direction;
using unswbc::Position;

struct Rival {
    int id = -1;
    int length_lower_bound = 2;
    int free_steps_lower_bound = 1;
    bool allowance_uncertain = true; // unseen segments and paid moves can make it faster
    std::vector<int> distance;
};

struct Model {
    struct Cell {
        Position position;
        bool occupied = false;
        bool pearl = false;
        int spawn_in = -1;
        std::array<int, 4> next{{-1, -1, -1, -1}};
    };
    int our_id = -1;
    int our_free_steps = 1;
    std::vector<Cell> cells;
    std::unordered_map<Position, int, unswbc::PositionHash> index;
    std::vector<int> our_distance;
    std::vector<bool> our_prior_food;
    std::vector<Rival> rivals;

    std::vector<int> distances(int start, std::vector<bool>* prior_food = nullptr) const {
        std::vector<int> result(cells.size(), -1), pending;
        if (prior_food) prior_food->assign(cells.size(), false);
        if (start < 0 || start >= static_cast<int>(cells.size())) return result;
        pending.reserve(cells.size()); pending.push_back(start); result[start] = 0;
        for (std::size_t front = 0; front < pending.size(); ++front) {
            const int at = pending[front];
            for (int next : cells[at].next) {
                if (next < 0 || cells[next].occupied) continue;
                if (result[next] < 0) {
                    result[next] = result[at] + 1; pending.push_back(next);
                }
                // All shortest-path parents are processed before this child.
                // Any possible intermediate food makes our later allowance
                // uncertain; do not claim the fixed-length ETA is exact.
                if (prior_food && result[next] == result[at] + 1
                    && ((*prior_food)[at] || (at != start
                        && (cells[at].pearl || (cells[at].spawn_in >= 1
                            && cells[at].spawn_in <= (result[at] - 1) / our_free_steps)))))
                    (*prior_food)[next] = true;
            }
        }
        return result;
    }

    double factor(Position goal, int our_path_steps) const {
        const auto found = index.find(goal);
        if (found == index.end() || our_path_steps <= 0) return 1.0;
        const int target = found->second;
        const auto& cell = cells[target];
        // A remembered pearl or an optimistic route outside today's window is
        // not evidence that a rival wins this contest. Keep the original weight.
        if (cell.occupied || (!cell.pearl && (cell.spawn_in < 1 || cell.spawn_in > 8))
            || target >= static_cast<int>(our_distance.size())
            || our_distance[target] != our_path_steps || our_prior_food[target]) return 1.0;
        const int spawn = cell.pearl ? 0 : cell.spawn_in;
        const int our_round = std::max(spawn, (our_path_steps - 1) / our_free_steps);
        double result = 1.0;
        for (const auto& rival : rivals) {
            const int steps = rival.distance[target];
            if (steps <= 0) continue;
            // Lower IDs have already acted at the time of our observation.
            // Their next opportunity is next round; later IDs still act now.
            const int first_round = rival.id < our_id ? 1 : 0;
            const int rival_round = std::max(spawn,
                first_round + (steps - 1) / rival.free_steps_lower_bound);
            const bool earlier_round = rival_round < our_round;
            const bool earlier_tie = rival_round == our_round && rival.id < our_id;
            if (!earlier_round && !earlier_tie) continue;
            // Future occupancy, choices and spawn success remain uncertain.
            // A countdown gets a gentle preference shift, never a veto.
            const double discount = cell.pearl ? (earlier_round ? 0.45 : 0.65)
                                               : (earlier_round ? 0.80 : 0.90);
            result = std::min(result, discount);
        }
        return result;
    }
};

inline Model build(const Controller& ct, const strategy::Memory& memory) {
    Model model;
    model.our_id = ct.get_id(); model.our_free_steps = std::max(1, (ct.get_length() + 3) / 4);
    const auto& tiles = ct.get_tiles();
    model.cells.reserve(tiles.size()); model.index.reserve(tiles.size());
    std::unordered_map<int, int> visible_lengths;
    for (const auto& tile : tiles) {
        const auto* part = tile.get_dragon();
        model.index.emplace(tile.get_position(), static_cast<int>(model.cells.size()));
        model.cells.push_back({tile.get_position(), part != nullptr,
                               tile.has_pearl(), tile.get_pearl_time(), {{-1, -1, -1, -1}}});
        if (part && part->get_team() != ct.get_team()) ++visible_lengths[part->get_id()];
    }
    for (auto& cell : model.cells) {
        int side = 0;
        for (auto direction : Direction::get_direction_list()) {
            Position destination;
            if (memory.destination(ct, cell.position, direction, destination)) {
                const auto found = model.index.find(destination);
                if (found != model.index.end()) cell.next[side] = found->second;
            }
            ++side;
        }
    }
    const auto ours = model.index.find(ct.get_position());
    model.our_distance = model.distances(ours == model.index.end() ? -1 : ours->second,
                                         &model.our_prior_food);
    for (const auto& tile : tiles) {
        const auto* part = tile.get_dragon();
        if (!part || !part->is_head() || part->get_team() == ct.get_team()) continue;
        Rival rival;
        rival.id = part->get_id();
        // Count is only a lower bound, even if every observed segment is close.
        // Minimum legal length is two; no inferred tail or total length is used.
        rival.length_lower_bound = std::max(2, visible_lengths[rival.id]);
        rival.free_steps_lower_bound = (rival.length_lower_bound + 3) / 4;
        rival.distance = model.distances(model.index.at(tile.get_position()));
        model.rivals.push_back(std::move(rival));
    }
    return model; // O((visible enemy heads + 1) * visible cells), at most 49 cells
}

inline double resource_factor(const Controller& ct, const strategy::Memory& memory,
                              Position goal, int our_path_steps) {
    return build(ct, memory).factor(goal, our_path_steps);
}
} // namespace contest
