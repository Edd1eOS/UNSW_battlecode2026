#include "../opponents/capital-transfer-v1/capital_transfer.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{20,20,64};Controller bot;strategy::Memory m;
    Scene(int id=0,Position center={5,5}):bot{id,Team::A,Direction::EAST,Vision{},64} {
        game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=center.y-3;y<=center.y+3;++y)for(int x=center.x-3;x<=center.x+3;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position=center;bot.unit_count=3;
    }
    void body(int id,std::deque<Position> b,Direction facing) {
        for(std::size_t i=0;i<b.size();++i){auto* t=bot.get_tile(b[i]);if(!t)continue;
            auto dir=facing;if(i)for(auto d:Direction::get_direction_list())if(b[i].add_dir(d)==b[i-1])dir=d;
            t->dragon_part=DragonPart{b[i],id,Team::A,dir,i==0};}
        if(id==bot.get_id()){m.body=b;bot.length=int(b.size());bot.head=*bot.get_tile(b.front())->get_dragon();}
    }
    void observe(int round=20){m.observe_map(bot,round);}
};
planner::Plan east(){return {{Direction::EAST,0},{Direction::EAST},"TEST",planner::Kind::Move,0,0,false};}
int main(){
    {Scene s;s.body(0,{{5,5},{4,5},{3,5}},Direction::EAST);s.body(2,{{7,5},{7,6}},Direction::NORTH);s.observe();
        transfer::State state;auto plan=east();auto out=transfer::prepare(s.bot,s.m,state,plan);
        assert(out.sonar&&state.donor==2&&state.drop==Position(7,5));auto g=transfer::unpack(out.sonar->second);
        assert(g&&g->queen==0&&g->donor==2&&g->round==20);
        s.bot.get_tile({6,4})->pearl=true;state={};plan=east();out=transfer::prepare(s.bot,s.m,state,plan);
        assert(!out.sonar); // Ordinary reachable food does not justify destroying a worker.
        s.bot.get_tile({6,4})->pearl=false;s.m.body.pop_back();state={};plan=east();
        assert(!transfer::prepare(s.bot,s.m,state,plan).sonar);}
    {Scene s(2,{7,5});s.body(2,{{7,5},{7,6}},Direction::NORTH);s.body(0,{{6,5},{5,5},{4,5}},Direction::EAST);s.observe();
        s.bot.sonar_messages={transfer::pack({2,20,0})};assert(transfer::donor_accepts(s.bot,s.m));
        auto plan=east();transfer::State state;auto out=transfer::prepare(s.bot,s.m,state,plan);
        assert(out.release&&plan.moves[0]==Direction::SOUTH);
        s.bot.sonar_messages={transfer::pack({2,19,0})};assert(!transfer::donor_accepts(s.bot,s.m));
        s.bot.sonar_messages={transfer::pack({2,20,0}),transfer::pack({2,20,0})};assert(!transfer::donor_accepts(s.bot,s.m));
        s.bot.sonar_messages={transfer::pack({2,20,0})};s.bot.unit_count=2;assert(!transfer::donor_accepts(s.bot,s.m));
        s.bot.unit_count=3;s.bot.get_tile({9,5})->dragon_part=DragonPart{{9,5},9,Team::B,Direction::WEST,true};
        assert(!transfer::donor_accepts(s.bot,s.m));}
    {Scene s(0,{6,5});s.body(0,{{6,5},{5,5},{4,5}},Direction::EAST);s.observe(21);s.bot.unit_count=2;
        transfer::State state{2,20,24,{7,5}};auto plan=east();s.bot.get_tile({7,5})->pearl=true;
        transfer::prepare(s.bot,s.m,state,plan);assert(plan.note=="CAPITAL_PICKUP observed=1"&&plan.food==1);
        s.bot.get_tile({7,5})->pearl=false;state={2,20,24,{7,5}};plan=east();
        transfer::prepare(s.bot,s.m,state,plan);assert(plan.note=="TEST");}
    std::cout<<"Transfer: projected offer, safe ordinary-food alternative, partial-body rejection, valid donor, stale/conflicting signals, survivor count, enemy contest, observed receipt passed\n";
}
