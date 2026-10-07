#include "../opponents/generalist-topology-v1/planner.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct Scene {
    Game board{20,12,64};Controller bot{0,Team::A,Direction::EAST,Vision{},64};strategy::Memory m;
    Scene(){game=&board;ct=&bot;m.width=20;m.height=12;m.cells.resize(240);
        for(auto& c:m.cells){c.known=true;for(auto& e:c.edges)e=Edge{false,EdgeType::KELP,-1};}}
    void link(Position a,Position b){bool found=false;for(auto d:Direction::get_direction_list())if(a.add_dir(d)==b){
        m.cells[m.index(a)].edges[strategy::Atlas::direction_index(d)]=Edge{};
        m.cells[m.index(b)].edges[strategy::Atlas::direction_index(d.get_opposite())]=Edge{};found=true;break;}assert(found);}
    strategy::Simulation body(Position current,Position previous){return {{current,previous},{},true,2};}
    void line(){for(int x=2;x<16;++x)link({x,5},{x+1,5});}
    void ring(){link({2,5},{2,4});link({2,4},{1,4});link({1,4},{1,5});link({1,5},{2,5});}
};
int main(){
    // Entering a long branch and leaving it are different states at one cell.
    {Scene s;s.line();s.ring();auto k=topology::build(s.m);
        auto in=k.at(s.m,s.body({4,5},{3,5})),out=k.at(s.m,s.body({3,5},{4,5}));
        assert(in.finite()&&in.remaining==12);assert(out.known&&out.cycle_possible&&!out.finite());}
    // The two directions of an ordinary edge are not a usable length-two loop.
    {Scene s;s.link({2,5},{3,5});auto k=topology::build(s.m);auto e=k.at(s.m,s.body({3,5},{2,5}));
        assert(e.finite()&&e.remaining==0);}
    // Unknown terrain is a possible outlet, never peeled into a false seal.
    {Scene s;s.line();s.m.cells[s.m.index({16,5})].known=false;auto k=topology::build(s.m);
        auto e=k.at(s.m,s.body({4,5},{3,5}));assert(e.known&&e.unknown_reachable&&!e.cycle_possible&&!e.finite());}
    // A portal without its partner stays unknown even inside an otherwise sealed tree.
    {Scene s;s.line();s.m.cells[s.m.index({16,5})].edges[strategy::Atlas::direction_index(Direction::EAST)]=Edge{false,EdgeType::PORTAL,71};
        auto k=topology::build(s.m);auto e=k.at(s.m,s.body({4,5},{3,5}));assert(e.unknown_reachable&&!e.finite());}
    // Multiple branches may reach a cycle and an unknown outlet independently.
    {Scene s;s.line();s.ring();s.link({2,5},{2,6});s.m.cells[s.m.index({2,6})].known=false;
        auto e=topology::build(s.m).at(s.m,s.body({3,5},{4,5}));assert(e.cycle_possible&&e.unknown_reachable);}
    // Full bodies may still fail in a small cycle: topology never proves fit.
    {Scene s;s.ring();auto e=topology::build(s.m).at(s.m,s.body({2,5},{1,5}));assert(e.cycle_possible);}
    // Unmodelled size and absent entering edges remain unresolved.
    {Scene s;auto e=topology::build(s.m).at(s.m,s.body({9,9},{8,9}));assert(!e.known&&!e.finite());
        s.m.cells.resize(8193);assert(!topology::build(s.m).available);}
    std::cout<<"Directed terrain kernel: long finite branch, direction, no neck reversal, unknown exit/portal, cycle and unresolved cap passed\n";
}
