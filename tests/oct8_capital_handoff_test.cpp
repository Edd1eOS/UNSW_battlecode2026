#ifdef OLD_BASELINE
#include "../opponents/v198-postmove-space/forage.hpp"
#else
#include "../opponents/v253-tail-capital-rescue/forage.hpp"
#endif
#include <cassert>
#include <iostream>
using namespace unswbc;

struct Scene {
    Game board{15,15,64};
    Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    forage::State state;
    Scene(int id=2) {
        game=&board;ct=&bot;board.round_num=100;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x)
            tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};
        bot.head={Position{5,5},id,Team::A,Direction::EAST,true};
        bot.length=8;bot.unit_count=8;
        memory.body={{5,5},{4,5},{3,5},{2,5},{2,4},{2,3},{3,3},{3,4}};
        place(memory.body,id,Team::A);
        place({{5,3},{6,3},{7,3}},3,Team::B);
        place({{7,5},{7,4},{6,4}},5,Team::B);
        place({{5,7},{6,7},{6,6}},7,Team::B);
        memory.observe(bot);
    }
    void place(const std::deque<Position>& body,int id,Team team) {
        for(std::size_t i=0;i<body.size();++i) {
            Direction toward_head=Direction::EAST;
            if(i) for(auto d:Direction::get_direction_list())
                if(body[i].add_dir(d)==body[i-1]) toward_head=d;
            bot.get_tile(body[i])->dragon_part=DragonPart{body[i],id,team,toward_head,i==0};
        }
    }
    strategy::Simulation finish(const forage::Plan& plan) {
        strategy::Simulation sim{memory.body,{},true,bot.length};
        const int free_steps=(bot.length+3)/4;
        for(int i=0;i<static_cast<int>(plan.moves.size());++i) {
            assert(strategy::simulate_step(bot,sim,plan.moves[i],&memory));
            if(i>=free_steps) {--sim.length;if(static_cast<int>(sim.body.size())>sim.length) sim.body.pop_back();}
        }
        return sim;
    }
    forage::Plan choose() { return forage::choose(bot,memory,state); }
    void wall(Direction d) {
        bot.get_tile(bot.get_position())->get_edge(d).edge_type=EdgeType::KELP;
        bot.get_tile(bot.get_position().add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;
    }
};

int main() {
 Scene s; auto p=s.choose();
 std::cout << "split="<<p.action.child_size<<" moves=";
 for(auto d:p.moves)std::cout<<d.value;
 std::cout<<" note="<<p.note<<"\n";
#ifndef OLD_BASELINE
 std::vector<double> risk(s.memory.cells.size(),0);
 strategy::Simulation sim{s.memory.body,{},true,8};
 bool used=capital_handoff::prefer(s.bot,s.memory,{Direction::SOUTH},risk,0);
 std::cout<<"forced-short-route="<<used<<"\n";
 // The original body and visible parent must be unchanged after projection.
 assert(s.bot.get_id()==2 && s.bot.length==8 && s.memory.body.size()==8);
 assert(s.bot.get_tile(s.memory.body[0])->get_dragon()->get_id()==2);
 Scene q(0);assert(!capital_handoff::prefer(q.bot,q.memory,{Direction::SOUTH},risk,0));
 Scene capacity;capacity.bot.unit_count=capacity.bot.unit_limit;
 assert(!capital_handoff::prefer(capacity.bot,capacity.memory,{Direction::SOUTH},risk,0));
 Scene partial;partial.memory.body.pop_back();
 assert(!capital_handoff::prefer(partial.bot,partial.memory,{Direction::SOUTH},risk,0));
#endif
}
