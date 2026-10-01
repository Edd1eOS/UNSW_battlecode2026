#include "helper.hpp"
#include "strategy.hpp"

int main() {
    // Official helper reads the protocol. ct controls our dragon.
    auto [ct, game] = unswbc::init();
    strategy::Memory memory;
    while (unswbc::update(ct, game)) {
        memory.observe(ct);
        memory.remember(ct.get_position());
        const auto direction = strategy::choose_move(ct, memory);
        ct.make_move(direction);
        unswbc::end_turn();
    }
}
