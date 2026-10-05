#include "../opponents/counterplay-prototype/forage.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{20, 20, 64};
    Controller bot{4, Team::A, Direction::EAST, Vision{}, 64};
    strategy::Memory memory;
    Scene(Position head = {5, 5}, int length = 4) {
        game = &board; ct = &bot; bot.head.position = head; bot.length = length;
        std::vector<Tile> tiles;
        for (int dy = -3; dy <= 3; ++dy) for (int dx = -3; dx <= 3; ++dx) {
            Position p{(head.x + dx + 20) % 20, (head.y + dy + 20) % 20};
            tiles.emplace_back(p, std::nullopt, -1);
            for (auto d : Direction::get_direction_list())
                tiles.back().get_edge(d) = Edge{false, EdgeType::KELP};
        }
        bot.vision = Vision{std::move(tiles)};
        bot.get_tile(head)->dragon_part = bot.head;
    }
    void open(Position at, Direction d) {
        bot.get_tile(at)->get_edge(d) = Edge{false, EdgeType::EMPTY};
        if (auto* next = bot.get_tile(at.add_dir(d)))
            next->get_edge(d.get_opposite()) = Edge{false, EdgeType::EMPTY};
    }
    void corridor() {
        for (int x = 5; x < 8; ++x) open({x, 5}, Direction::EAST);
        open({7, 5}, Direction::NORTH); open({7, 4}, Direction::NORTH);
    }
    void enemy(Position p, int id = 7, bool head = true) {
        bot.get_tile(p)->dragon_part = DragonPart{p, id, Team::B, Direction::SOUTH, head};
    }
    void pearl(Position p) { bot.get_tile(p)->pearl = true; }
    contest::Model model() { memory.observe_map(bot, 20); return contest::build(bot, memory); }
};
bool same(double a, double b) { return std::abs(a - b) < 1e-9; }

int main() {
    // A visible rival one step from corridor food discounts our three-step trip.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.pearl({7, 4});
      auto m = s.model(); assert(same(m.factor({7, 4}, 3), 0.45));
      assert(m.rivals.size() == 1 && m.rivals[0].length_lower_bound == 2);
      assert(m.rivals[0].allowance_uncertain && m.rivals[0].free_steps_lower_bound == 1);
      assert(same(m.factor({8, 5}, 3), 1.0)); } // no resource
    // We act now. A later enemy cannot win a current-turn free-step tie.
    { Scene s; s.open({5, 5}, Direction::EAST); s.open({6, 5}, Direction::EAST);
      s.enemy({7, 5}); s.pearl({6, 5}); auto m = s.model();
      assert(same(m.factor({6, 5}, 1), 1.0)); }
    // An earlier enemy has already acted now, but wins a next-round ID tie.
    { Scene s; s.corridor(); s.enemy({7, 3}, 1); s.pearl({7, 4});
      auto m = s.model(); assert(same(m.factor({7, 4}, 3), 0.45));
      s.bot.length = 8; m = s.model(); assert(same(m.factor({7, 4}, 3), 0.65));
      s.bot.length = 12; m = s.model(); assert(same(m.factor({7, 4}, 3), 1.0)); }
    // Equal future-round arrivals favor the lower ID; a later-ID tie is neutral.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.bot.get_tile({7, 4})->pearl_time = 2;
      auto m = s.model(); assert(same(m.factor({7, 4}, 3), 1.0));
      s.enemy({7, 3}, 1); m = s.model(); assert(same(m.factor({7, 4}, 3), 0.90)); }
    // Fresh countdowns are a softer economic hint than a present pearl.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.bot.get_tile({7, 4})->pearl_time = 1;
      auto m = s.model(); assert(same(m.factor({7, 4}, 3), 0.80));
      s.bot.get_tile({7, 4})->pearl_time = 9; m = s.model();
      assert(same(m.factor({7, 4}, 3), 1.0)); }
    // Current bodies block the corridor; their future departure is not assumed.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.pearl({7, 5});
      s.bot.get_tile({7, 4})->dragon_part = DragonPart{{7, 4}, 9, Team::A, Direction::NORTH, false};
      auto m = s.model(); assert(same(m.factor({7, 5}, 2), 1.0));
      s.pearl({7, 4}); m = s.model(); assert(same(m.factor({7, 4}, 3), 1.0)); }
    // A known portal is one edge. Only a currently visible exit may participate.
    { Scene s; s.corridor(); s.enemy({8, 3}); s.pearl({7, 4});
      s.bot.get_tile({8, 3})->get_edge(Direction::SOUTH) = Edge{false, EdgeType::PORTAL, 31};
      s.bot.get_tile({7, 3})->get_edge(Direction::SOUTH) = Edge{false, EdgeType::PORTAL, 31};
      s.bot.get_tile({7, 4})->get_edge(Direction::NORTH) = Edge{false, EdgeType::PORTAL, 31};
      auto m = s.model(); assert(m.rivals[0].distance[m.index.at({7, 4})] == 1);
      assert(same(m.factor({7, 4}, 3), 0.45));
      s.memory.portals[31].resize(1); m = contest::build(s.bot, s.memory);
      assert(same(m.factor({7, 4}, 3), 1.0)); }
    // Ordinary paths cross the toroidal seam within the actual 7x7 observation.
    { Scene s({0, 5}); s.open({0, 5}, Direction::WEST); s.open({19, 5}, Direction::WEST);
      s.open({18, 5}, Direction::NORTH); s.enemy({18, 4}); s.pearl({18, 5});
      auto m = s.model(); assert(same(m.factor({18, 5}, 2), 0.45)); }
    // Five observed segments prove at least two free moves, not an exact length.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.pearl({7, 5});
      for (auto p : std::vector<Position>{{6, 3}, {5, 3}, {4, 3}, {3, 3}}) s.enemy(p, 7, false);
      auto m = s.model(); assert(m.rivals[0].length_lower_bound == 5);
      assert(m.rivals[0].free_steps_lower_bound == 2 && m.rivals[0].allowance_uncertain);
      assert(same(m.factor({7, 5}, 2), 0.45)); }
    // Old hidden food/terrain/head hints and unknown own paths cannot discount.
    { Scene s; s.corridor(); s.pearl({7, 4}); auto m = s.model();
      assert(same(m.factor({7, 4}, 3), 1.0));
      auto& hidden = s.memory.cells[s.memory.index({9, 5})];
      hidden.known = true; hidden.pearl = true; hidden.seen = s.memory.now;
      s.memory.body.push_back({9, 5}); // memory never supplies rival occupancy
      s.enemy({7, 3}); m = contest::build(s.bot, s.memory);
      assert(same(m.factor({9, 5}, 4), 1.0));
      assert(same(m.factor({7, 4}, 2), 1.0)); // inconsistent/optimistic supplied route
      assert(same(m.factor({7, 4}, 99), 1.0)); }
    // Intermediate food can increase our next-turn free allowance. Preserve
    // the baseline rather than treating our starting allowance as permanent.
    { Scene s; s.corridor(); s.enemy({7, 3}); s.pearl({7, 4}); s.pearl({6, 5});
      auto m = s.model(); assert(m.our_prior_food[m.index.at({7, 4})]);
      assert(same(m.factor({7, 4}, 3), 1.0));
      s.bot.get_tile({6, 5})->pearl = false;
      s.bot.get_tile({7, 5})->pearl_time = 1; m = s.model();
      assert(same(m.factor({7, 4}, 3), 1.0));
      s.bot.get_tile({7, 5})->pearl_time = 9; m = s.model();
      assert(same(m.factor({7, 4}, 3), 0.45)); }
    // The integrated planner chooses a slightly farther uncontested resource,
    // rather than just calculating a factor that never changes the goal.
    { Scene s;s.corridor();s.enemy({7,3});s.pearl({7,4});
      s.open({5,5},Direction::WEST);s.open({4,5},Direction::WEST);
      s.open({3,5},Direction::NORTH);s.open({3,4},Direction::NORTH);s.pearl({3,3});
      s.memory.observe_map(s.bot,20);forage::State state;
      const auto selected=forage::select_goal(s.bot,s.memory,state);
#if COUNTER_FOOD_RACE
      assert(selected==s.memory.index({3,3}));assert(state.resource_contests==1);
#else
      assert(selected==s.memory.index({7,4}));assert(state.resource_contests==0);
#endif
    }
    std::cout << "Visible resource contests: corridor, turn order, countdown, occupancy, portals, wrap and length bounds passed.\n";
}
