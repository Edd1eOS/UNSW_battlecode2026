#pragma once
#include "strategy.hpp"

// Evidence about the action being emitted, under the current observation.
// This is not a promise about other dragons' later actions or future vision.
namespace action_evidence {
using namespace strategy;
enum class Status { Confirmed, Unresolved, Rejected, Sacrifice };
enum class Reason { None, Affordability, MissingOrigin, Wall, Portal, Vision,
                    OwnBody, Blocked, ForeignBody, EmptyAction, SplitRule, ModelGap };
struct Result {
    Status status=Status::Unresolved;
    Reason reason=Reason::ModelGap;
    int verified_steps=0, food=0, paid=0, target_id=-1;
    bool target_friendly=false, target_head=false;
};
inline const char* label(Status s) {
    switch(s) { case Status::Confirmed:return "confirmed"; case Status::Unresolved:return "unknown";
                case Status::Rejected:return "rejected"; case Status::Sacrifice:return "sacrifice"; }
    return "unknown";
}
inline Result advance(const Controller& ct,const Memory& m,Simulation& s,Direction d,
                      bool paid,const std::vector<Position>& blocked={}) {
    if(paid&&s.length<=2)return {Status::Rejected,Reason::Affordability};
    if(s.body.empty())return {Status::Unresolved,Reason::MissingOrigin};
    const auto* from=ct.get_tile(s.body.front());
    if(!from)return {Status::Unresolved,Reason::MissingOrigin};
    Position to;
    if(!m.destination(ct,s.body.front(),d,to))
        return {from->get_edge(d).is_portal()?Status::Unresolved:Status::Rejected,
                from->get_edge(d).is_portal()?Reason::Portal:Reason::Wall};
    if(std::find(blocked.begin(),blocked.end(),to)!=blocked.end())
        return {Status::Rejected,Reason::Blocked};
    if(std::find(s.body.begin(),s.body.end(),to)!=s.body.end())
        return {Status::Rejected,Reason::OwnBody};
    const auto* tile=ct.get_tile(to);
    if(!tile)return {Status::Unresolved,Reason::Vision};
    if(const auto* part=tile->get_dragon()) {
        if(part->get_id()!=ct.get_id()||!s.complete) {
            Result r{Status::Rejected,part->get_id()==ct.get_id()?Reason::OwnBody:Reason::ForeignBody};
            r.target_id=part->get_id();r.target_friendly=part->get_team()==ct.get_team();
            r.target_head=part->is_head();return r;
        }
    }
    const int before=static_cast<int>(s.eaten.size());
    if(!simulate_step(ct,s,d,&m))return {Status::Unresolved,Reason::ModelGap};
    if(paid){--s.length;if(static_cast<int>(s.body.size())>s.length)s.body.pop_back();}
    return {Status::Confirmed,Reason::None,1,static_cast<int>(s.eaten.size())-before,paid?1:0};
}
inline Result audit(const Controller& ct,const Memory& m,const std::vector<Direction>& moves,
                    int child=0,bool deliberate_enemy_queen_trade=false) {
    if(child>0)return {ct.can_split(child)?Status::Confirmed:Status::Rejected,
                      ct.can_split(child)?Reason::None:Reason::SplitRule};
    if(moves.empty())return {Status::Rejected,Reason::EmptyAction};
    Simulation s{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
    if(s.body.empty())s.body.push_back(ct.get_position());
    Result total{Status::Confirmed,Reason::None};
    const int free=(ct.get_length()+3)/4;
    for(std::size_t i=0;i<moves.size();++i) {
        // Facing establishes the neck even when the full body is unavailable.
        if(i==0&&ct.get_length()>=2&&moves[i]==ct.get_dir().get_opposite())
            return {Status::Rejected,Reason::OwnBody,total.verified_steps,total.food,total.paid};
        auto r=advance(ct,m,s,moves[i],static_cast<int>(i)>=free);
        if(r.status!=Status::Confirmed) {
            if(r.status==Status::Rejected&&r.reason==Reason::ForeignBody&&r.target_head
               &&!r.target_friendly&&r.target_id<=1&&deliberate_enemy_queen_trade&&i+1==moves.size())
                r.status=Status::Sacrifice;
            // An unknown step may only be the final emitted step. We never
            // certify instructions after an unobserved transition.
            if(r.status==Status::Unresolved&&i+1<moves.size())r.status=Status::Rejected;
            r.verified_steps=total.verified_steps;r.food=total.food;r.paid=total.paid;
            return r;
        }
        total.verified_steps+=r.verified_steps;total.food+=r.food;total.paid+=r.paid;
    }
    return total;
}
}
