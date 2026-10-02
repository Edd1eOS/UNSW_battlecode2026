#pragma once
#include "helper.hpp"
#include <algorithm>
#include <queue>

namespace strategy {
// 只记亲眼见过的地形。珍珠会过期；绝不把旧敌人位置当作当前障碍。
struct Atlas {
    struct Cell {
        bool known = false;
        bool pearl = false;
        int seen = -1000;
        std::array<unswbc::Edge, 4> edges{};
    };
    struct Mouth { unswbc::Position base; bool horizontal; };
    int width = 0, height = 0, now = 0;
    std::vector<Cell> cells;
    std::unordered_map<int, std::vector<Mouth>> portals;
    int index(unswbc::Position p) const { return p.y * width + p.x; }
    const Cell* cell(unswbc::Position p) const {
        if (p.x < 0 || p.y < 0 || p.x >= width || p.y >= height) return nullptr;
        return &cells[index(p)];
    }
    static int direction_index(unswbc::Direction d) {
        const auto dirs = unswbc::Direction::get_direction_list();
        return static_cast<int>(std::find(dirs.begin(), dirs.end(), d) - dirs.begin());
    }
    static Mouth mouth(unswbc::Position p, unswbc::Direction d) {
        using D = unswbc::Direction;
        bool horizontal = d == D(D::NORTH) || d == D(D::SOUTH);
        if (d == D(D::NORTH) || d == D(D::WEST)) p = p.add_dir(d);
        return {p, horizontal}; // 用边的北/西侧格子表示，同一扇门两侧只记一次。
    }
    void observe_map(const unswbc::Controller& ct, int round) {
        if (!unswbc::game) return;
        auto [w, h] = unswbc::game->get_map_size();
        if (width != w || height != h) {
            width = w; height = h; cells.assign(w * h, {}); portals.clear();
        }
        now = round;
        for (const auto& tile : ct.get_tiles()) {
            auto& c = cells[index(tile.get_position())];
            c.known = true; c.pearl = tile.has_pearl(); c.seen = now;
            int i = 0;
            for (auto d : unswbc::Direction::get_direction_list()) {
                const auto& edge = tile.get_edge(d);
                c.edges[i++] = edge;
                if (!edge.is_portal()) continue;
                auto m = mouth(tile.get_position(), d);
                auto& pair = portals[edge.get_portal_id()];
                if (std::none_of(pair.begin(), pair.end(), [&](const Mouth& x) {
                    return x.base == m.base && x.horizontal == m.horizontal;
                })) pair.push_back(m);
            }
        }
    }
    // true 只表示地形出口已知，不表示出口无人。
    bool destination(const unswbc::Controller& ct, unswbc::Position p,
                     unswbc::Direction d, unswbc::Position& out) const {
        const auto* tile = ct.get_tile(p);
        const auto* c = cell(p);
        if (!tile && (!c || !c->known)) return false;
        const auto& edge = tile ? tile->get_edge(d) : c->edges[direction_index(d)];
        if (edge.get_edge_type() == unswbc::EdgeType::KELP) return false;
        if (!edge.is_portal()) { out = p.add_dir(d); return true; }
        const auto it = portals.find(edge.get_portal_id());
        if (it == portals.end() || it->second.size() != 2) return false;
        auto entry = mouth(p, d);
        const auto& pair = it->second;
        int which = pair[0].base == entry.base && pair[0].horizontal == entry.horizontal ? 0 : 1;
        if (pair[which].base != entry.base || pair[which].horizontal != entry.horizontal) return false;
        const auto& other = pair[1 - which];
        if (other.horizontal != entry.horizontal) return false;
        out = other.base;
        using D = unswbc::Direction;
        if (d == D(D::EAST) || d == D(D::SOUTH)) out = out.add_dir(d);
        return true;
    }
    // 在已经发现的地图上找目标，未知格只算探索边界；不是透视全图。
    double route_value(const unswbc::Controller& ct, unswbc::Position start) const {
        if (!cell(start)) return 0;
        std::vector<int> distance(cells.size(), -1);
        std::queue<unswbc::Position> pending;
        pending.push(start); distance[index(start)] = 0;
        double best = 0;
        int budget = 2048; // 大地图也给搜索一个明确上限。
        while (!pending.empty() && budget-- > 0) {
            auto p = pending.front(); pending.pop();
            int depth = distance[index(p)];
            const auto& c = cells[index(p)];
            if (!c.known) { best = std::max(best, 22.0 / (depth + 2)); continue; }
            const auto* live = ct.get_tile(p);
            if (live && live->get_dragon()) continue;
            if (c.pearl && now - c.seen <= 12)
                best = std::max(best, (live ? 85.0 : 40.0) / (depth + 1));
            for (auto d : unswbc::Direction::get_direction_list()) {
                unswbc::Position next;
                if (!destination(ct, p, d, next)) {
                    if (ct.get_id() > 1 && c.edges[direction_index(d)].is_portal())
                        best = std::max(best, 28.0 / (depth + 2));
                    continue;
                }
                if (!cell(next) || distance[index(next)] >= 0) continue;
                distance[index(next)] = depth + 1; pending.push(next);
            }
        }
        return best;
    }
};
} // namespace strategy
