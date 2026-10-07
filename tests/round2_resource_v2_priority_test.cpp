#include "../opponents/generalist-resource-priority-v2/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{15,15,64};Controller bot{2,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory m;
    Scene(){game=&board;ct=&bot;std::vector<Tile> tiles;
        for(int y=2;y<=8;++y)for(int x=2;x<=8;++x)tiles.emplace_back(Position{x,y},std::nullopt,-1);
        bot.vision=Vision{std::move(tiles)};bot.head.position={5,5};bot.length=3;bot.unit_count=3;
        m.body={{5,5},{4,5},{3,5}};
        for(auto p:m.body)bot.get_tile(p)->dragon_part=DragonPart{p,2,Team::A,Direction::EAST,p==Position(5,5)};
        bot.get_tile({6,3})->dragon_part=DragonPart{{6,3},0,Team::A,Direction::EAST,true};
        bot.get_tile({6,4})->pearl=true;bot.get_tile({7,4})->pearl=true;
        m.observe_map(bot,100);}
    resource_priority::Field field(std::vector<resource_priority::Ally> allies={{0,{6,3},3}},std::vector<bool> danger={}){
        return resource_priority::build(bot,m,allies,danger);}
};
int main(){
    {Scene s;auto f=s.field();assert(f.beneficiary==0&&f.marked==1);
        assert(f.opportunity_cost[s.m.index({6,4})]==65&&f.opportunity_cost[s.m.index({7,4})]==0);
        auto sim=planner::initial(s.bot,s.m);sim.eaten={{6,4},{7,4}};assert(f.cost(s.m,sim)==65);
        assert(110-f.cost(s.m,sim)>0);}
    {Scene s;auto f=s.field({{4,{6,3},12},{0,{6,3},3}});assert(f.beneficiary==0);
        f=s.field({{4,{6,3},7}});assert(f.beneficiary==-1);
        f=s.field({{4,{6,3},8}});assert(f.beneficiary==4&&f.marked==2);
        assert(f.opportunity_cost[s.m.index({6,4})]==45);
        s.bot.length=8;assert(s.field({{4,{6,3},8}}).beneficiary==-1);}
    {Scene s;std::vector<bool> danger(s.m.cells.size());danger[s.m.index({6,4})]=true;
        assert(s.field({{0,{6,3},3}},danger).marked==0);
        s.bot.get_tile({6,4})->dragon_part=DragonPart{{6,4},9,Team::B,Direction::NORTH,false};
        assert(s.field().marked==0);}
    {Scene s;s.bot.get_tile({6,3})->get_edge(Direction::SOUTH)=Edge{false,EdgeType::PORTAL,73};
        s.m.observe_map(s.bot,100);assert(s.field().marked==0);}
    {Scene s;s.m.now=499;assert(s.field().beneficiary==-1);
        assert(s.field({{4,{6,3},8}}).beneficiary==4);}
    {Scene s;s.bot.head.dragon_id=0;assert(s.field({{4,{6,3},12}}).beneficiary==-1);}
    std::cout<<"Resource priority: conservative reach, soft positive food utility, Queen priority, length lower bound, occupancy/threat/portal and final action order passed\n";
}
