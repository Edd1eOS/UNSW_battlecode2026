#include "../opponents/adversarial-reply-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{20,20,64};Controller bot{0,Team::A,Direction::EAST,Vision{},64};strategy::Memory m;
    Scene(){game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.unit_count=3;
        body(0,{{5,5},{4,5},{3,5}},Direction::EAST);
    }
    void body(int id,std::deque<Position> b,Direction facing){
        for(std::size_t i=0;i<b.size();++i){auto* t=bot.get_tile(b[i]);if(!t)continue;
            auto dir=facing;if(i)for(auto d:Direction::get_direction_list())if(b[i].add_dir(d)==b[i-1])dir=d;
            t->dragon_part=DragonPart{b[i],id,id==0?Team::A:Team::B,dir,i==0};}
        if(id==0){m.body=b;bot.length=int(b.size());bot.head=*bot.get_tile(b.front())->get_dragon();}
    }
    reply_search::Result run(){m.observe_map(bot,20);return reply_search::assess(bot,m,planner::initial(bot,m));}
};
int main(){
    {Scene s;s.body(2,{{8,5},{8,6},{7,6},{6,6}},Direction::WEST);auto r=s.run();
        assert(r.status==reply_search::Status::Witness&&r.enemy==2&&r.steps==3&&r.expanded<=320);}
    {Scene s;s.body(2,{{7,5},{7,6}},Direction::NORTH);assert(s.run().status!=reply_search::Status::Witness);
        s.bot.get_tile({6,5})->pearl=true;auto r=s.run();assert(r.status==reply_search::Status::Witness&&r.steps==2);
        auto queen=planner::initial(s.bot,s.m);queen.eaten.push_back({6,5});
        assert(reply_search::assess(s.bot,s.m,queen).status!=reply_search::Status::Witness);}
    {Scene s;s.body(2,{{7,5},{6,5}},Direction::EAST);assert(s.run().status!=reply_search::Status::Witness);}
    {Scene s;s.body(2,{{8,5},{8,6}},Direction::NORTH);assert(s.run().status==reply_search::Status::Unknown);}
    {Scene s;s.body(2,{{7,5},{7,6}},Direction::NORTH);s.m.observe_map(s.bot,20);
        auto queen=planner::initial(s.bot,s.m);queen.complete=false;
        assert(reply_search::assess(s.bot,s.m,queen).status==reply_search::Status::Unknown);}
    {Scene s;auto r=s.run();assert(r.status==reply_search::Status::NoWitness&&r.expanded==0);}
    {planner::Candidate paid,free;paid.kind=free.kind=planner::Kind::Move;paid.paid=1;paid.food=0;
     paid.future.depth=free.future.depth=8;paid.enemy_risk=2;free.enemy_risk=1;
     free.reply.status=reply_search::Status::Witness;paid.reply.status=reply_search::Status::NoWitness;
     assert(!planner::capital_dominated(paid,free,8));
     free.reply.status=reply_search::Status::NoWitness;assert(planner::capital_dominated(paid,free,8));}
    std::cout<<"Reply search: paid three-step collision, affordability, food funding, consumed pearl, own-neck block, partial body, absent enemy passed\n";
}
