#pragma once
#include "planner.hpp"

// A local, one-step delivery contract. Sonar is a proposal, never authenticated
// evidence. No claims about unseen allies, enemy actions, or future receipts.
namespace transfer {
using namespace planner;
struct State { int donor=-1,issued=-1000,next_offer=0;Position drop; };
struct Output { bool release=false;std::optional<std::pair<Direction,std::uint64_t>> sonar; };
struct Grant {int donor,round,queen;};
inline std::uint64_t pack(Grant g) {
    return (std::uint64_t{0x36}<<26)|(std::uint64_t(g.queen)<<25)|(std::uint64_t(g.round)<<16)|g.donor;
}
inline std::optional<Grant> unpack(std::uint64_t v) {
    if((v>>26)!=0x36)return {};
    return Grant{int(v&65535),int((v>>16)&511),int((v>>25)&1)};
}
inline const unswbc::DragonPart* head(const Controller& ct,int id) {
    for(const auto& t:ct.get_tiles())if(t.get_dragon()&&t.get_dragon()->get_id()==id&&t.get_dragon()->is_head())return t.get_dragon();
    return nullptr;
}
// Unlike a visible prefix, this proves the small donor has no hidden tail.
inline std::deque<Position> small_body(const Controller& ct,int id) {
    const auto* h=head(ct,id);if(!h)return {};
    std::deque<Position> body{h->get_position()};
    for(int n=0;n<4;++n) {
        const auto* tail=ct.get_tile(body.back());if(!tail)return {};
        std::optional<Position> predecessor;
        for(auto d:Direction::get_direction_list()) {
            const auto& edge=tail->get_edge(d);if(edge.is_portal())return {};
            if(edge.get_edge_type()==EdgeType::KELP)continue;
            const auto* t=ct.get_tile(body.back().add_dir(d));if(!t)return {};
            const auto* p=t->get_dragon();if(!p||p->get_id()!=id||p->is_head())continue;
            if(t->get_edge(p->get_dir()).get_edge_type()!=EdgeType::EMPTY)return {};
            if(t->get_position().add_dir(p->get_dir())!=body.back())continue;
            if(predecessor||std::find(body.begin(),body.end(),t->get_position())!=body.end())return {};
            predecessor=t->get_position();
        }
        if(!predecessor) {
            int seen=0;for(const auto& t:ct.get_tiles())if(t.get_dragon()&&t.get_dragon()->get_id()==id)++seen;
            return seen==int(body.size())&&body.size()>=2&&body.size()<=3?body:std::deque<Position>{};
        }
        body.push_back(*predecessor);if(body.size()>3)return {};
    }
    return {};
}
inline int distance(Position a,Position b) {
    auto [w,h]=unswbc::game->get_map_size();int x=std::abs(a.x-b.x),y=std::abs(a.y-b.y);
    return std::min(x,w-x)+std::min(y,h-y);
}
inline bool quiet(const Controller& ct,int queen,int donor,Position drop) {
    for(const auto& t:ct.get_tiles())if(const auto* p=t.get_dragon()) {
        if(p->get_team()!=ct.get_team())return false;
        if(p->is_head()&&p->get_id()!=queen&&p->get_id()!=donor&&distance(t.get_position(),drop)<=2)return false;
    }
    return true;
}
inline std::optional<Direction> adjacent(const Controller& ct,Position from,Position to) {
    const auto* tile=ct.get_tile(from);if(!tile)return {};
    for(auto d:Direction::get_direction_list())if(tile->get_edge(d).get_edge_type()==EdgeType::EMPTY&&from.add_dir(d)==to)return d;
    return {};
}
inline bool donor_accepts(const Controller& ct,const Memory& m) {
    if(ct.get_id()<=1||ct.get_id()>65535||ct.get_length()>3||ct.get_length()<2||ct.get_unit_count()<3
       ||m.body.size()!=std::size_t(ct.get_length())||m.now>=499)return false;
    std::optional<Grant> grant;
    for(auto message:ct.get_sonar_messages()) {
        auto g=unpack(message);if(!g||g->donor!=ct.get_id()||g->round!=m.now)continue;
        if(grant)return false;grant=g;
    }
    if(!grant)return false;
    const auto* q=head(ct,grant->queen);
    if(!q||q->get_team()!=ct.get_team()||!quiet(ct,grant->queen,ct.get_id(),ct.get_position()))return false;
    auto direction=adjacent(ct,q->get_position(),ct.get_position());
    if(!direction||*direction==q->get_dir().get_opposite())return false;
    // The only emitted fatal action must hit our own known neck, never another
    // head. A message cannot override this physical check.
    const auto ev=action_evidence::audit(ct,m,{ct.get_dir().get_opposite()});
    return ev.status==action_evidence::Status::Rejected&&ev.reason==action_evidence::Reason::OwnBody;
}
inline bool future_safe(const Controller& ct,const Memory& m,const Simulation& s) {
    int budget=100;return continuation(ct,m,s,{},0,8,budget).depth>=8;
}
inline Output prepare(const Controller& ct,const Memory& m,State& state,Plan& plan) {
    Output out;
    if(ct.get_id()>1) {
        if(donor_accepts(ct,m)) {
            const auto d=ct.get_dir().get_opposite();
            plan={{d,0},{d},"CAPITAL_RELEASE length="+std::to_string(ct.get_length()),Kind::Fallback,0,0,false};
            out.release=true;
        }
        return out;
    }
    if(state.donor>=0&&m.now==state.issued+1) {
        const auto* tile=ct.get_tile(state.drop);auto d=adjacent(ct,ct.get_position(),state.drop);
        auto s=initial(ct,m);
        if(tile&&tile->has_pearl()&&!head(ct,state.donor)&&d&&plan.food==0&&s.complete
           &&quiet(ct,ct.get_id(),state.donor,state.drop)&&step(ct,m,s,*d,false)&&future_safe(ct,m,s))
            plan={{*d,0},{*d},"CAPITAL_PICKUP observed=1",Kind::Move,1,0,false};
    }
    state.donor=-1;
    if(m.now>=499||m.now<state.next_offer||ct.get_unit_count()<3||plan.action.child_size||plan.moves.empty()||plan.uncertain)return out;
    auto projected=initial(ct,m);if(!projected.complete)return out;
    const int free=(ct.get_length()+3)/4;
    for(std::size_t i=0;i<plan.moves.size();++i)if(!step(ct,m,projected,plan.moves[i],int(i)>=free))return out;
    Controller scene=ct;scene.head.position=projected.body.front();scene.head.dir=plan.moves.back();scene.length=projected.length;
    Memory future=m;future.body=projected.body;
    for(auto p:projected.eaten)if(auto* tile=scene.get_tile(p))tile->pearl=false;
    // Do not destroy a worker for a one-pearl offer if an ordinary adjacent
    // pearl already has an equally confirmed continuation.
    for(auto d:Direction::get_direction_list()) {
        auto next=projected;const int before=int(next.eaten.size());
        if(step(scene,future,next,d,false)&&int(next.eaten.size())>before&&future_safe(scene,future,next))return out;
    }
    for(const auto& tile:scene.get_tiles()) {
        const auto* p=tile.get_dragon();if(!p||!p->is_head()||p->get_team()!=ct.get_team()||p->get_id()<=1||p->get_id()>65535)continue;
        const int donor=p->get_id();auto direction=adjacent(scene,projected.body.front(),tile.get_position());
        if(!direction||!quiet(scene,ct.get_id(),donor,tile.get_position()))continue;
        auto body=small_body(scene,donor);if(body.empty())continue;
        Controller released=scene;
        for(auto& cell:released.vision.tiles)if(cell.get_dragon()&&cell.get_dragon()->get_id()==donor)cell.dragon_part.reset();
        for(std::size_t i=0;i<body.size();i+=2)released.get_tile(body[i])->pearl=true;
        auto next=projected;
        if(!step(released,future,next,*direction,false)||!future_safe(released,future,next))continue;
        out.sonar=std::make_pair(*direction,pack({donor,m.now,ct.get_id()}));
        state.donor=donor;state.issued=m.now;state.drop=body.front();state.next_offer=m.now+4;
        plan.note+=" CAPITAL_OFFER donor="+std::to_string(donor);break;
    }
    return out;
}
}
