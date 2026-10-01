#include "../opponents/v3-experimental/strategy.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Fixture {
    Game board{11, 11, 64};
    Controller bot{0, Team::A, Direction::NORTH, Vision{}, 64};
    Fixture() {
        game = &board;
        ct = &bot;
        std::vector<Tile> tiles;
        for (int y = 2; y <= 8; ++y)
            for (int x = 2; x <= 8; ++x) tiles.emplace_back(Position{x, y});
        bot.vision = Vision{std::move(tiles)};
        bot.head.position = {5, 5};
        bot.get_tile({5, 5})->dragon_part = bot.head;
    }
    void wall(Position p, Direction d) {
        bot.get_tile(p)->get_edge(d).edge_type = EdgeType::KELP;
        if (auto* other = bot.get_tile(p.add_dir(d)))
            other->get_edge(d.get_opposite()).edge_type = EdgeType::KELP;
    }
};

int main() {
    {
        Fixture f;
        f.bot.get_tile({6, 5})->pearl = true;
        assert(strategy::choose_move(f.bot, {}) == Direction(Direction::EAST));
    }
    {
        Fixture f;
        f.bot.get_tile({6, 5})->pearl = true;
        f.wall({5, 5}, Direction::EAST);
        assert(!strategy::ordinary_step(f.bot, {5, 5}, Direction::EAST));
        assert(strategy::choose_move(f.bot, {}) != Direction(Direction::EAST));
    }
    {
        Fixture f;
        // Our tail is occupied even though it might move later this turn.
        f.bot.get_tile({6, 5})->dragon_part = DragonPart{{6, 5}, 0, Team::A, Direction::WEST, false};
        assert(!strategy::ordinary_step(f.bot, {5, 5}, Direction::EAST));
    }
    {
        Fixture f;
        // A tempting pearl inside a one-cell dead end must lose to open space.
        f.bot.get_tile({6, 5})->pearl = true;
        f.wall({6, 5}, Direction::NORTH);
        f.wall({6, 5}, Direction::EAST);
        f.wall({6, 5}, Direction::SOUTH);
        assert(strategy::evaluate(f.bot, {6, 5}).space == 1);
        assert(strategy::choose_move(f.bot, {}) != Direction(Direction::EAST));
    }
    {
        Fixture f;
        auto& portal = f.bot.get_tile({5, 5})->get_edge(Direction::EAST);
        portal = Edge{false, EdgeType::PORTAL, 7};
        assert(!strategy::ordinary_step(f.bot, {5, 5}, Direction::EAST));
        for (auto d : {Direction::NORTH, Direction::SOUTH, Direction::WEST}) f.wall({5, 5}, d);
        assert(strategy::choose_move(f.bot, {}) == Direction(Direction::EAST));
    }
    {
        Fixture f;
        f.bot.get_tile({7, 5})->dragon_part = DragonPart{{7, 5}, 1, Team::B, Direction::WEST, true};
        assert(strategy::nearby_threats(f.bot, {6, 5}) == 1);
        f.wall({7, 5}, Direction::WEST);
        assert(strategy::nearby_threats(f.bot, {6, 5}) == 0);
    }
    {
        Fixture f;
        assert((Position{0, 0}.add_dir(Direction::WEST) == Position{10, 0}));
        assert((Position{0, 0}.add_dir(Direction::NORTH) == Position{0, 10}));
        auto e = strategy::evaluate(f.bot, {6, 5});
        assert(e.space == 48); // Unknown cells must not inflate the count.
        assert(e.frontier_distance < 1000);
    }
    {
        Fixture f;
        f.bot.get_tile({5, 4})->dragon_part = DragonPart{{5,4},0,Team::A,Direction::SOUTH,false};
        f.bot.get_tile({6, 4})->dragon_part = DragonPart{{6,4},0,Team::A,Direction::WEST,false};
        strategy::Memory memory;
        memory.observe(f.bot);
        assert(memory.body.size() == 3);
        assert((memory.body.back() == Position{6,4}));
        strategy::Simulation state{memory.body, {}, true, 3};
        assert(strategy::simulate_step(f.bot, state, Direction::EAST));
        // Tail has now vacated (6,4), so we can enter on the NEXT turn.
        assert(strategy::simulate_step(f.bot, state, Direction::NORTH));
    }
    {
        Fixture f;
        f.bot.get_tile({6,5})->pearl = true;
        strategy::Simulation state{{Position{5,5},Position{5,4},Position{6,4}}, {}, true, 3};
        assert(strategy::simulate_step(f.bot, state, Direction::EAST));
        assert(state.length == 4 && state.body.size() == 4);
        assert(!strategy::simulate_step(f.bot, state, Direction::NORTH));
    }
    {
        Fixture f;
        strategy::Simulation state{{Position{5,5},Position{5,4},Position{6,4},Position{6,5}}, {}, true, 4};
        // Moving onto the tail is illegal even on a non-growing turn.
        assert(!strategy::simulate_step(f.bot, state, Direction::EAST));
    }
    {
        Fixture f;
        f.bot.get_tile({6,5})->pearl = true;
        strategy::Simulation state{{Position{5,5}}, {Position{6,5}}, true, 1};
        assert(strategy::simulate_step(f.bot, state, Direction::EAST));
        assert(state.length == 1); // Already eaten pearls cannot grow us twice.
    }
    {
        Fixture f;
        strategy::Simulation state{{Position{5,5}}, {}, false, 10};
        assert(strategy::simulate_step(f.bot, state, Direction::EAST));
        assert(state.body.size() == 2); // Unknown tail cannot release known head prematurely.
        assert(!strategy::simulate_step(f.bot, state, Direction::WEST));
    }
    {
        Fixture f;
        for (Position p : {Position{6,5},Position{7,5}}) {
            f.wall(p, Direction::NORTH); f.wall(p, Direction::SOUTH);
        }
        f.wall({7,5}, Direction::EAST);
        auto result = strategy::look_ahead(f.bot, {}, Direction::EAST);
        assert(result.depth == 2 && !result.uncertain);
        assert(strategy::choose_move(f.bot, {}) != Direction(Direction::EAST));
        strategy::Simulation state{{Position{5,5}}, {}, false, 3};
        int zero_budget = 0;
        assert(strategy::search_survival(f.bot, state, 0, 8, zero_budget).uncertain);
    }
    {
        Fixture f;
        f.bot.head.dir = Direction::EAST;
        f.bot.get_tile({7,5})->pearl = true;
        f.bot.get_tile({5,3})->pearl = true;
        f.bot.get_tile({8,5})->dragon_part = DragonPart{{8,5},1,Team::B,Direction::WEST,true};
        auto arrival = strategy::enemy_arrival(f.bot);
        const auto* pearl = f.bot.get_tile({7,5});
        assert(arrival[pearl - f.bot.get_tiles().data()] == 1);
        // Equally distant pearls, but the eastern one is closer to the enemy.
        assert(strategy::choose_move(f.bot, {}) == Direction(Direction::NORTH));
        f.wall({8,5}, Direction::WEST);
        arrival = strategy::enemy_arrival(f.bot);
        assert(arrival[pearl - f.bot.get_tiles().data()] > 1);
    }
    {
        Fixture f;
        f.bot.get_tile({6,5})->pearl = true;
        auto arrival = strategy::enemy_arrival(f.bot);
        assert(strategy::evaluate(f.bot, {6,5}, &arrival).pearl_reward == 70.0);
    }
    std::cout << "15 strategy scenarios passed\n";
}
