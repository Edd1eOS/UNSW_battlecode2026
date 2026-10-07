#include "../opponents/generalist-evidence-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
using action_evidence::Status;
using action_evidence::Reason;
struct Scene {
    Game board{15,15,64};Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory m;
    Scene(){game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=3;bot.unit_count=2;
        m.body={{5,5},{4,5},{3,5}};
        for(auto p:m.body)bot.get_tile(p)->dragon_part=DragonPart{p,0,Team::A,Direction::EAST,p==Position(5,5)};
        m.observe_map(bot,0);}
};
int main(){
    {Scene s;s.bot.get_tile({6,5})->pearl=true;s.bot.get_tile({7,5})->pearl=true;
        auto r=action_evidence::audit(s.bot,s.m,{Direction::EAST,Direction::EAST});
        assert(r.status==Status::Confirmed&&r.food==2&&r.paid==1&&r.verified_steps==2);}
    {Scene s;auto r=action_evidence::audit(s.bot,s.m,{Direction::WEST});
        assert(r.status==Status::Rejected&&r.reason==Reason::OwnBody);}
    {Scene s;s.bot.get_tile({5,5})->get_edge(Direction::NORTH)=Edge{false,EdgeType::KELP,-1};
        auto r=action_evidence::audit(s.bot,s.m,{Direction::NORTH});assert(r.status==Status::Rejected&&r.reason==Reason::Wall);}
    {Scene s;s.bot.get_tile({5,5})->get_edge(Direction::NORTH)=Edge{false,EdgeType::PORTAL,73};
        auto r=action_evidence::audit(s.bot,s.m,{Direction::NORTH});assert(r.status==Status::Unresolved&&r.reason==Reason::Portal);
        r=action_evidence::audit(s.bot,s.m,{Direction::NORTH,Direction::EAST});assert(r.status==Status::Rejected);}
    {Scene s;auto sim=planner::initial(s.bot,s.m);sim.body={{10,10},{9,10}};sim.length=2;
        auto r=action_evidence::advance(s.bot,s.m,sim,Direction::EAST,false);assert(r.status==Status::Unresolved&&r.reason==Reason::MissingOrigin);
        r=action_evidence::advance(s.bot,s.m,sim,Direction::EAST,true);assert(r.status==Status::Rejected&&r.reason==Reason::Affordability);}
    {Scene s;s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},1,Team::B,Direction::WEST,true};
        assert(action_evidence::audit(s.bot,s.m,{Direction::EAST}).status==Status::Rejected);
        assert(action_evidence::audit(s.bot,s.m,{Direction::EAST},0,true).status==Status::Sacrifice);
        s.bot.get_tile({6,5})->dragon_part=DragonPart{{6,5},2,Team::A,Direction::WEST,true};
        assert(action_evidence::audit(s.bot,s.m,{Direction::EAST},0,true).status==Status::Rejected);}
    {Scene s;assert(action_evidence::audit(s.bot,s.m,{},2).status==Status::Rejected);
        s.bot.length=6;assert(action_evidence::audit(s.bot,s.m,{},2).status==Status::Confirmed);
        s.bot.unit_count=64;assert(action_evidence::audit(s.bot,s.m,{},2).status==Status::Rejected);}
    std::cout<<"Action contract: cost order, neck, wall, unknown portal/origin, no steps after unknown, explicit sacrifice and split legality passed\n";
}
