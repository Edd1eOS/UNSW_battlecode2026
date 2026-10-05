#ifdef OLD_BASELINE
#include "../opponents/v66-queen-threat-buffer/forage.hpp"
#include <optional>
namespace selected {
struct Attack { std::vector<unswbc::Direction> moves; std::string note; };
inline std::optional<Attack> attack_queen(const unswbc::Controller& ct,
                                        const strategy::Memory& memory, bool ordinary = false) {
    auto moves = forage::attack_queen(ct, memory, ordinary);
    if (moves.empty()) return std::nullopt;
    return Attack{std::move(moves), "baseline"};
}
}
#else
#include "../opponents/counterplay-prototype/counter_attack.hpp"
namespace selected = counterplay;
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{17,17,64};
    Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    Scene() {
        game = &board; ct = &bot; board.round_num = 100;
        std::vector<Tile> tiles;
        for (int y=2; y<=8; ++y) for (int x=2; x<=8; ++x) {
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
            for (auto dir : Direction::get_direction_list()) tiles.back().get_edge(dir).edge_type=EdgeType::KELP;
        }
        bot.vision=Vision{std::move(tiles)}; bot.head.position={5,5}; bot.unit_count=10;
        own_body({{5,5},{5,6},{5,7},{4,7}});
    }
    void open(Position at, Direction dir) {
        bot.get_tile(at)->get_edge(dir)=Edge{false,EdgeType::EMPTY};
        if (auto* next=bot.get_tile(at.add_dir(dir))) next->get_edge(dir.get_opposite())=Edge{false,EdgeType::EMPTY};
    }
    void part(Position at, int id, bool head=false, Direction dir=Direction::NORTH) {
        bot.get_tile(at)->dragon_part=DragonPart{at,id,id%2?Team::B:Team::A,dir,head};
    }
    void own_body(std::initializer_list<Position> cells) {
        for (auto& tile:bot.vision.tiles)
            if (tile.get_dragon() && tile.get_dragon()->get_id()==bot.get_id()) tile.dragon_part.reset();
        memory.body.assign(cells); bot.length=static_cast<int>(cells.size());
        bot.head.position=memory.body.front();
        bot.get_tile(bot.get_position())->dragon_part=bot.head;
        for (std::size_t i=1; i<memory.body.size(); ++i) {
            for (auto dir:Direction::get_direction_list()) if (memory.body[i].add_dir(dir)==memory.body[i-1]) {
                part(memory.body[i],bot.get_id(),false,dir); open(memory.body[i],dir); break;
            }
        }
    }
    void worker(int id, std::initializer_list<Position> cells) {
        auto previous=cells.begin(); part(*previous,id,true);
        for (auto cell=std::next(previous); cell!=cells.end(); ++cell) {
            bool linked=false;
            for (auto dir:Direction::get_direction_list()) if (cell->add_dir(dir)==*previous) {
                part(*cell,id,false,dir); open(*cell,dir); linked=true; break;
            }
            assert(linked); previous=cell;
        }
        if (cells.size()>1) {
            const auto neck=std::next(cells.begin());
            for (auto dir:Direction::get_direction_list()) if (neck->add_dir(dir)==*cells.begin())
                bot.get_tile(*cells.begin())->dragon_part->dir=dir;
        }
    }
    std::optional<selected::Attack> choose(bool ordinary=false) {
        memory.observe_map(bot,board.round_num);
        return selected::attack_queen(bot,memory,ordinary);
    }
    void legal(const selected::Attack& attack, int target_id, int paid, int expected_length) {
        Position end=bot.get_position();
        for (auto dir:attack.moves) {
            Position next; assert(memory.destination(bot,end,dir,next)); end=next;
        }
        auto* tile=bot.get_tile(end); assert(tile && tile->get_dragon());
        assert(tile->get_dragon()->is_head() && tile->get_dragon()->get_id()==target_id);
        auto saved=tile->dragon_part; tile->dragon_part.reset();
        strategy::Simulation sim{memory.body,{},true,bot.length};
        int charged=0; const int free=(bot.length+3)/4;
        for (std::size_t i=0; i<attack.moves.size(); ++i) {
            const bool cost=static_cast<int>(i)>=free;
            if (cost) assert(sim.length>2);
            assert(strategy::simulate_step(bot,sim,attack.moves[i],&memory));
            if (cost) { ++charged; --sim.length; if (static_cast<int>(sim.body.size())>sim.length) sim.body.pop_back(); }
        }
        tile->dragon_part=saved;
        assert(charged==paid && sim.length==expected_length);
        assert(static_cast<int>(sim.body.size())==sim.length);
    }
};

int main() {
    // The visible Queen is sealed. Its existence used to hide a reachable guard.
    { Scene s; s.part({8,5},1,true,Direction::WEST); s.worker(3,{{6,5},{6,6},{6,7},{7,7}}); s.open({5,5},Direction::EAST);
      assert(!s.choose()); auto attack=s.choose(true);
#ifdef OLD_BASELINE
      assert(!attack);
#else
      assert(attack && attack->moves.size()==1 && attack->moves.front()==Direction(Direction::EAST));
      s.legal(*attack,3,0,4);
#endif
    }
    // A reachable Queen retains priority over a longer, cheaper ordinary target.
    { Scene s; s.worker(1,{{5,3},{5,2}}); s.open({5,5},Direction::NORTH); s.open({5,4},Direction::NORTH);
      s.worker(3,{{6,5},{6,6},{6,7},{7,7},{7,6},{7,5}}); s.open({5,5},Direction::EAST);
      auto attack=s.choose(true); assert(attack && attack->moves.size()==2 && attack->moves.front()==Direction(Direction::NORTH));
      s.legal(*attack,1,1,3);
    }
    // An inaccessible larger worker must not suppress a reachable eligible one.
    { Scene s; s.worker(3,{{8,5},{8,6},{8,7},{7,7},{7,6},{7,5}});
      s.worker(5,{{6,5},{6,6},{6,7},{6,8}}); s.open({5,5},Direction::EAST);
      auto attack=s.choose(true);
#ifdef OLD_BASELINE
      assert(!attack);
#else
      assert(attack && attack->moves.size()==1); s.legal(*attack,5,0,4);
#endif
    }
    // Equal visible lower bounds use the shorter route, not vision iteration order.
    { Scene s; s.worker(3,{{5,3},{5,2},{4,2},{3,2}}); s.open({5,5},Direction::NORTH); s.open({5,4},Direction::NORTH);
      s.worker(5,{{6,5},{6,6},{6,7},{7,7}}); s.open({5,5},Direction::EAST);
      auto attack=s.choose(true); assert(attack);
#ifdef OLD_BASELINE
      assert(attack->moves.size()==2); s.legal(*attack,3,1,3);
#else
      assert(attack->moves.size()==1); s.legal(*attack,5,0,4);
#endif
    }
    // Preserve the original economics and role gates.
    { Scene s; s.worker(3,{{6,5},{6,6},{6,7},{7,7},{7,6},{7,5}}); s.open({5,5},Direction::EAST);
      assert(!s.choose()); s.bot.unit_count=9; assert(!s.choose(true));
      s.part({8,5},3,false,Direction::WEST); s.open({8,5},Direction::WEST); assert(s.choose(true));
      s.bot.unit_count=2; assert(!s.choose(true)); s.bot.unit_count=3; assert(s.choose(true));
      s.own_body({{5,5},{5,6},{5,7},{4,7},{4,6}}); assert(!s.choose(true));
      s.own_body({{5,5},{5,6},{5,7},{4,7}});
      s.bot.head.dragon_id=0; assert(!s.choose(true));
    }
    // Two units may trade for Queen only while our Queen's live head is visible.
    { Scene s; s.bot.unit_count=2; s.open({5,5},Direction::EAST); s.open({6,5},Direction::EAST);
      s.worker(1,{{7,5},{8,5}}); assert(!s.choose(true));
      s.worker(0,{{3,3},{3,4}}); auto attack=s.choose();
#ifdef OLD_BASELINE
      assert(!attack);
#else
      assert(attack && attack->moves.size()==2); s.legal(*attack,1,1,3);
      attack=s.choose(true); assert(attack); s.legal(*attack,1,1,3);
#endif
      // The prior head sighting, and a current Queen body pointing out of view,
      // cannot substitute for a currently visible friendly Queen head.
      s.bot.get_tile({3,3})->dragon_part.reset(); s.bot.get_tile({3,4})->dragon_part.reset();
      s.part({4,2},0,false,Direction::NORTH); s.open({4,2},Direction::NORTH); assert(!s.choose(true));
      s.bot.get_tile({4,2})->dragon_part.reset(); s.worker(4,{{3,3},{3,4}});
      assert(!s.choose(true)); // A visible friendly ordinary head is insufficient.
      s.bot.get_tile({3,3})->dragon_part.reset(); s.bot.get_tile({3,4})->dragon_part.reset();
      s.worker(0,{{3,3},{3,4}}); s.bot.unit_count=1; assert(!s.choose(true));
      s.bot.unit_count=2;
      s.bot.get_tile({7,5})->dragon_part.reset(); s.bot.get_tile({8,5})->dragon_part.reset();
      s.worker(3,{{7,5},{7,6},{7,7},{8,7},{8,6},{8,5},{8,4}});
      assert(!s.choose(true)); // Even a profitable ordinary trade still needs three units.
      s.bot.unit_count=3; attack=s.choose(true); assert(attack); s.legal(*attack,3,1,3);
    }
    // L4 has one free step plus two paid steps. Food does not raise free quota.
    { Scene s; for (int x=5; x<8; ++x) s.open({x,5},Direction::EAST); s.part({8,5},1,true,Direction::WEST);
      auto attack=s.choose(); assert(attack && attack->moves.size()==3); s.legal(*attack,1,2,2);
      s.bot.get_tile({6,5})->pearl=true; s.bot.get_tile({7,5})->pearl=true;
      attack=s.choose(); assert(attack && attack->moves.size()==3); s.legal(*attack,1,2,4);
      s.bot.get_tile({8,5})->dragon_part.reset(); s.worker(1,{{8,4},{7,4}}); s.open({8,5},Direction::NORTH);
      assert(!s.choose()); // Keep the conservative original length budget even with food.
    }
    { Scene s; s.own_body({{5,5},{5,6}}); s.open({5,5},Direction::EAST); s.open({6,5},Direction::EAST); s.worker(1,{{7,5},{8,5}});
      assert(!s.choose()); s.own_body({{5,5},{5,6},{5,7}});
      auto attack=s.choose(); assert(attack && attack->moves.size()==2); s.legal(*attack,1,1,2);
    }
    // A resolved portal is one move; its adjacent tile is not the destination.
    { Scene s; s.part({8,5},1,true,Direction::WEST); s.part({6,5},6,false,Direction::WEST); s.part({7,5},6,true,Direction::WEST);
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({7,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,7};
      s.bot.get_tile({8,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,7};
      auto attack=s.choose(); assert(attack && attack->moves.size()==1); s.legal(*attack,1,0,4);
    }
    { Scene s; s.worker(1,{{6,5},{7,5}});
      s.bot.get_tile({5,5})->get_edge(Direction::EAST)=Edge{false,EdgeType::PORTAL,99};
      s.bot.get_tile({6,5})->get_edge(Direction::WEST)=Edge{false,EdgeType::PORTAL,99};
      assert(!s.choose()); // No guessed unresolved portal exit.
    }
    // Current enemy bodies, allied bodies, other heads and our old tail are blockers.
    for (int blocker : {7,6,3}) {
      Scene s; for (int x=5; x<8; ++x) s.open({x,5},Direction::EAST); s.part({8,5},1,true,Direction::WEST);
      if (blocker==3) s.worker(3,{{6,5},{6,4}});
      else s.worker(blocker,{{6,4},{6,5}});
      assert(!s.choose(true));
    }
    { Scene s; s.own_body({{5,5},{6,5},{6,6},{5,6}});
      s.open({6,5},Direction::EAST); s.open({7,5},Direction::EAST); s.part({8,5},1,true,Direction::WEST); assert(!s.choose());
    }
#ifdef OLD_BASELINE
    std::cout << "Frozen v66 reproduces target masking and longer equal-value route; legality and gates pass.\n";
#else
    std::cout << "Reachable target selection, Queen priority, economics, paid/body accounting and portals pass.\n";
#endif
}
