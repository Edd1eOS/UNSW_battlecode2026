#include "../bot/strategy.hpp"

// Read a recorded protocol stream from stdin and explain candidate moves.
// This diagnoses a fixed observation sequence, not a new live match.
int main() {
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        auto head = ct.get_position();
        std::cout << "ROUND " << game.get_round_num()
                  << " HEAD " << head.x << "," << head.y
                  << " length " << ct.get_length()
                  << " known " << memory.body.size();
        int child = strategy::emergency_split_size(ct);
        if (child > 0) std::cout << " SPLIT " << child << "\n";
        else std::cout << " MOVE " << strategy::choose_move(ct, memory) << "\n";
        for (auto direction : unswbc::Direction::get_direction_list()) {
            if (!strategy::ordinary_step(ct, head, direction)) continue;
            auto region = strategy::evaluate(ct, head.add_dir(direction));
            auto future = strategy::look_ahead(ct, memory, direction);
            std::cout << direction << " space=" << region.space
                      << " pearl_distance=" << region.pearl_distance
                      << " exits=" << region.exits << " depth=" << future.depth
                      << " uncertain=" << future.uncertain << "\n";
        }
    }
}
