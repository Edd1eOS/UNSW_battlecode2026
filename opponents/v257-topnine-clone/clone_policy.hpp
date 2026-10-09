#pragma once
#include "forage.hpp"
namespace topclone {
using namespace strategy;
using MacroFeatures=std::array<double,16>;
inline MacroFeatures features(const Controller& ct,const Memory& m) {
    MacroFeatures f{};f[0]=ct.get_id()<=1;f[1]=ct.get_length();f[2]=m.now;
    f[3]=ct.get_unit_count();f[6]=99;f[14]=99;
    for(const auto& t:ct.get_tiles()) {
        if(t.has_pearl())++f[11];
        const auto* p=t.get_dragon();if(!p || !p->is_head() || p->get_id()==ct.get_id())continue;
        const int dd=forage::distance(m,ct.get_position(),t.get_position());
        if(p->get_team()!=ct.get_team()){++f[4];f[14]=std::min(f[14],double(dd));continue;}
        ++f[5];if(p->get_id()<=1)f[6]=std::min(f[6],double(dd));
        int seen=0;for(const auto& q:ct.get_tiles())if(q.get_dragon()&&q.get_dragon()->get_id()==p->get_id())++seen;
        f[7]+=seen>ct.get_length();f[8]=std::max(f[8],double(seen));
    }
    for(auto d:Direction::get_direction_list()) {
        Position n;
        if(ct.get_tile(ct.get_position())->get_edge(d).get_edge_type()==EdgeType::KELP)++f[15];
        if(!m.destination(ct,ct.get_position(),d,n))continue;
        auto t=ct.get_tile(n);if(t&&!t->get_dragon()){++f[9];f[10]+=t->has_pearl();}
    }
    if(static_cast<int>(m.body.size())==ct.get_length() && ct.get_tile(m.body.back())) {
        f[12]=1;
        for(auto d:Direction::get_direction_list()) {
            Position n;if(!m.destination(ct,m.body.back(),d,n))continue;
            auto t=ct.get_tile(n);if(t&&!t->get_dragon())++f[13];
        }
    }
    return f;
}
inline int classify(const MacroFeatures& f) {
    int at=0;
    while(NODES[at].f>=0) {const auto& n=NODES[at];at=f[n.f]<=n.v?n.l:n.r;}
    return int(std::max_element(NODES[at].p,NODES[at].p+5)-NODES[at].p);
}
inline forage::Plan choose(const Controller& ct,Memory& m,forage::State& state) {
    const auto f=features(ct,m);const int action=classify(f);
    int child=action==1?2:action==2?ct.get_length()/2:action==3?ct.get_length()-2:0;
    if(child && ct.can_split(child))
        return {{ct.get_dir(),child},{},"V257 LEARNED_SPLIT class="+std::to_string(action)};
    if(action==4 && ct.get_id()>1 && ct.get_unit_count()>1) {
        for(auto d:Direction::get_direction_list()) {
            Position n;if(!m.destination(ct,ct.get_position(),d,n))continue;
            auto t=ct.get_tile(n);auto p=t?t->get_dragon():nullptr;
            if(p && p->get_id()==ct.get_id() && !p->is_head())
                return {{d,0},{d},"V257 LEARNED_DELIVERY"};
        }
    }
    auto plan=forage::choose_movement(ct,m,state);
    // Keep the existing last-resort physical rescue when the model asks to move
    // but its selected first step is a known collision.
    Simulation sim{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
    if(!plan.moves.empty() && !simulate_step(ct,sim,plan.moves.front(),&m)) {
        int rescue=emergency_split_size(ct);
        if(rescue>0){plan.action.child_size=rescue;plan.moves.clear();plan.note="V257 PHYSICAL_RESCUE";}
    }
    return plan;
}
}
