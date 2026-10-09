#pragma once
#include "strategy.hpp"
#include "terrain.hpp"
#include "born_threat.hpp"
#include "investment.hpp"
#include "roles.hpp"
#include <cmath>

// One bounded candidate pipeline. All information comes from this unit's input.
namespace planner {
using namespace strategy;
enum class Kind { Move, Split, QueenTrade, UnknownPortal, Fallback };
struct Future { int depth=0; bool outside=false, portal=false, exhausted=false; int next_free_food=0; };
struct PendingBody {
    bool active=false, expected_head_known=false;
    Position expected_head;
    std::deque<Position> prefix_history;
    int minimum_length=0,maximum_length=0;
};
struct State {
    bool reserve=false;
    int old_length=0, last_food=-1000, goal=-1, goal_since=-1000;
    PendingBody pending;
    regional_role::State region;
};
struct Candidate {
    Kind kind=Kind::Move;
    Simulation simulation;
    std::vector<Direction> moves;
    std::vector<Position> blocked;
    int child=0, food=0, paid=0;
    bool uncertain=false, imminent=false, birth_possible=false;
    double score=-1e30, risk=0, enemy_risk=0;
    Future future;
    bool ordinary_investment=false;
    std::optional<investment::Forecast> joint;
    int investment_rejection=0; // 1 parent closure, 2 child closure, 3 capital
};
struct Plan { Decision action; std::vector<Direction> moves; std::string note; Kind kind; int food=0,paid=0; bool uncertain=false; };

inline bool contains(const std::vector<Position>& points,Position p) {
    return std::find(points.begin(),points.end(),p)!=points.end();
}
inline Simulation initial(const Controller& ct,const Memory& m) {
    Simulation s{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
    if(s.body.empty()) s.body.push_back(ct.get_position());
    return s;
}
// Engine actions.cc: affordability -> old-body collision -> food/ordinary tail
// removal -> paid tail removal. A pearl cannot finance a step at length two.
inline bool step(const Controller& ct,const Memory& m,Simulation& s,Direction d,
                 bool paid,const std::vector<Position>& blocked={}) {
    if(paid && s.length<=2) return false;
    Position target;
    if(!m.destination(ct,s.body.front(),d,target) || contains(blocked,target)) return false;
    if(!simulate_step(ct,s,d,&m)) return false;
    if(paid) { --s.length; if(static_cast<int>(s.body.size())>s.length) s.body.pop_back(); }
    return true;
}
inline Future continuation(const Controller& ct,const Memory& m,const Simulation& s,
                           const std::vector<Position>& blocked,int depth,int horizon,int& budget,
                           int initial_food=-1,int next_free=-1,int prefix_food=0) {
    if(initial_food<0)initial_food=static_cast<int>(s.eaten.size());
    if(next_free<0)next_free=(s.length+3)/4;
    const int food=depth<=next_free?static_cast<int>(s.eaten.size())-initial_food:prefix_food;
    if(depth>=horizon) return {depth,false,false,false,food};
    if(budget--<=0) return {depth,false,false,true};
    Future best{depth,false,false,false,food};
    const auto* tile=ct.get_tile(s.body.front());
    if(!tile) return {depth,true,false,false};
    auto dirs=Direction::get_direction_list();
    std::stable_sort(dirs.begin(),dirs.end(),[&](Direction a,Direction b){
        Position aa,bb;const auto* ta=m.destination(ct,s.body.front(),a,aa)?ct.get_tile(aa):nullptr;
        const auto* tb=m.destination(ct,s.body.front(),b,bb)?ct.get_tile(bb):nullptr;
        bool fa=ta&&ta->has_pearl()&&!contains(s.eaten,aa),fb=tb&&tb->has_pearl()&&!contains(s.eaten,bb);
        return fa>fb;
    });
    for(auto d:dirs) {
        Position to;
        if(!m.destination(ct,s.body.front(),d,to)) {
            if(tile->get_edge(d).is_portal()) best.portal=true;
            continue;
        }
        if(contains(blocked,to) || std::find(s.body.begin(),s.body.end(),to)!=s.body.end()) continue;
        if(!ct.get_tile(to)) {best.outside=true;continue;}
        Simulation next=s;
        if(!step(ct,m,next,d,false,blocked)) continue;
        auto f=continuation(ct,m,next,blocked,depth+1,horizon,budget,initial_food,next_free,food);
        // Depth and food estimate must describe the same continuation. A
        // pearl in a dead short branch cannot subsidize a different escape.
        if(f.depth>=horizon)return f;
        if(f.depth>best.depth || (f.depth==best.depth&&f.next_free_food>best.next_free_food)) {
            best.depth=f.depth;best.next_free_food=f.next_free_food;
        }
        best.outside=best.outside||f.outside;best.portal=best.portal||f.portal;
        best.exhausted=best.exhausted||f.exhausted;
    }
    return best;
}
inline std::vector<Position> observed_chain(const Controller& ct,const Memory& m,int id) {
    std::vector<Position> chain;
    for(const auto& t:ct.get_tiles()) if(t.get_dragon() && t.get_dragon()->get_id()==id && t.get_dragon()->is_head())
        chain.push_back(t.get_position());
    if(chain.empty()) return chain;
    for(int k=0;k<48;++k) {
        bool found=false;
        for(const auto& t:ct.get_tiles()) {
            auto* p=t.get_dragon();Position to;
            if(!p || p->get_id()!=id || p->is_head() || contains(chain,t.get_position())) continue;
            if(m.destination(ct,t.get_position(),p->get_dir(),to) && to==chain.back()) {
                chain.push_back(t.get_position());found=true;break;
            }
        }
        if(!found) break;
    }
    return chain;
}
inline int head_reach(const Controller& ct,const Memory& m,const unswbc::Tile& t) {
    auto chain=observed_chain(ct,m,t.get_dragon()->get_id());
    bool complete=!chain.empty();
    if(complete) for(auto d:Direction::get_direction_list()) {
        Position to;
        const auto* tail=ct.get_tile(chain.back());
        if(tail->get_edge(d).get_edge_type()==EdgeType::KELP) continue;
        if(!m.destination(ct,chain.back(),d,to) || !ct.get_tile(to)) complete=false;
    }
    int length=static_cast<int>(chain.size());
    return std::min(8,complete?std::max(1,(length+3)/4+length-2):std::max(3,(length+3)/4+length-2));
}
inline std::vector<double> risks(const Controller& ct,const Memory& m,std::vector<bool>* imminent=nullptr,
                                 std::vector<double>* enemy_risk=nullptr) {
    std::vector<double> risk(m.cells.size(),0);
    if(imminent)imminent->assign(m.cells.size(),false);
    if(enemy_risk)enemy_risk->assign(m.cells.size(),0);
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon();
        if(!p || !p->is_head() || p->get_id()==ct.get_id()) continue;
        bool enemy=p->get_team()!=ct.get_team();
        if(!enemy && p->get_id()<ct.get_id()) continue;
        const int reach=enemy?head_reach(ct,m,t):std::min(4,std::max(1,static_cast<int>(observed_chain(ct,m,p->get_id()).size()+3)/4));
        std::queue<Position> q;std::vector<int> dist(m.cells.size(),-1);
        q.push(t.get_position());dist[m.index(t.get_position())]=0;
        while(!q.empty()) {
            Position at=q.front();q.pop();int n=dist[m.index(at)];if(n>=reach)continue;
            for(auto d:Direction::get_direction_list()) {
                Position to;if(!m.destination(ct,at,d,to)||!m.cell(to)||dist[m.index(to)]>=0)continue;
                const auto* live=ct.get_tile(to);if(!live)continue;
                const auto* part=live->get_dragon();
                // Over-approximate vacated own/enemy body, do not rely on it as a shield.
                if(part && part->get_id()!=p->get_id() && part->get_id()!=ct.get_id())continue;
                dist[m.index(to)]=n+1;q.push(to);
                // Keep direct visible-head contact separate from accumulated
                // soft reach weights. The enemy cannot step into its old body.
                if(imminent && enemy && n==0 && (!part||part->get_id()!=p->get_id()))
                    (*imminent)[m.index(to)]=true;
                const double weight=enemy?(n==0?1.0:(n==1?0.35:0.12/(n-1))):(n==0?0.35:0.08);
                risk[m.index(to)]+=weight;
                if(enemy&&enemy_risk)(*enemy_risk)[m.index(to)]+=weight;
            }
        }
    }
    return risk;
}
struct GoalGraph { std::vector<int> distance,field; int goal=-1,food_sites=0,frontiers=0; double value=0; };
inline GoalGraph goals(const Controller& ct,const Memory& m,State& state) {
    GoalGraph g;const int size=static_cast<int>(m.cells.size());
    g.distance.assign(size,9999);g.field.assign(size,9999);
    std::vector<std::vector<int>> reverse(size);
    std::vector<double> value(size,0);
    std::queue<Position> q;q.push(ct.get_position());g.distance[m.index(ct.get_position())]=0;
    int budget=2048;
    while(!q.empty() && budget-->0) {
        auto at=q.front();q.pop();int i=m.index(at),depth=g.distance[i];const auto& c=m.cells[i];
        if(!c.known) continue;
        const auto* live=ct.get_tile(at);
        if((live && live->has_pearl()) || (c.pearl && m.now-c.seen<=10)) {
            value[i]=(live?110.0:45.0)/(1.0+0.18*depth);++g.food_sites;
        } else if(c.spawn_round>=m.now && c.spawn_round<=m.now+8) {
            const int eta=(depth+std::max(1,(ct.get_length()+3)/4)-1)/std::max(1,(ct.get_length()+3)/4);
            value[i]=25.0/(1.0+0.2*depth+std::abs(c.spawn_round-m.now-eta));
            ++g.food_sites;
        }
        bool frontier=false;
        for(auto d:Direction::get_direction_list()) {
            Position to;
            if(!m.destination(ct,at,d,to)) {if(c.edges[Atlas::direction_index(d)].is_portal())frontier=true;continue;}
            if(!m.cell(to))continue;
            const auto* t=ct.get_tile(to);const auto* part=t?t->get_dragon():nullptr;
            if(part && part->get_id()!=ct.get_id())continue;
            int j=m.index(to);reverse[j].push_back(i);
            if(!m.cells[j].known)frontier=true;
            if(g.distance[j]==9999){g.distance[j]=depth+1;q.push(to);}
        }
        if(frontier) {++g.frontiers;value[i]+=((m.now-state.last_food>=12)?45.0:15.0)/(1+0.12*depth);}
        value[i]-=std::min(20,m.lifetime_visits(at))*(m.now-state.last_food>=12?2.0:0.4);
        if(i==m.index(ct.get_position()) && !c.pearl) value[i]-=15;
        if(value[i]>g.value) {g.value=value[i];g.goal=i;}
    }
    if(state.goal>=0 && state.goal<size && g.distance[state.goal]<9999 && m.now-state.goal_since<10
       && value[state.goal]>0 && value[state.goal]*1.3>=g.value) {g.goal=state.goal;g.value=value[state.goal];}
    if(g.goal!=state.goal) {state.goal=g.goal;state.goal_since=m.now;}
    if(g.goal<0) return g;
    std::queue<int> pending;pending.push(g.goal);g.field[g.goal]=0;
    while(!pending.empty()) {int at=pending.front();pending.pop();for(int before:reverse[at])
        if(g.field[before]==9999){g.field[before]=g.field[at]+1;pending.push(before);}}
    return g;
}
inline bool friendly_queen(const Controller& ct) {
    for(const auto& t:ct.get_tiles()) {const auto* p=t.get_dragon();
        if(p&&p->is_head()&&p->get_id()<=1&&p->get_team()==ct.get_team())return true;}
    return false;
}
inline void update_role(const Controller& ct,const Memory& m,State& state) {
    if(ct.get_length()>state.old_length) state.last_food=m.now;
    state.old_length=ct.get_length();
#ifdef INVESTMENT_KEEP_V5_ROLES
    if(ct.get_id()>1 && ((ct.get_length()>=8 && ct.get_unit_count()>=3)
        || (m.reserve_worker && m.splits_done>=1))) state.reserve=true;
    // Deliberately no population-based demotion: current capital remains a reserve.
#else
    state.reserve=regional_role::update(ct,m,state.region,[&](int id){return static_cast<int>(observed_chain(ct,m,id).size());});
#endif
}
inline bool protected_asset(const Controller& ct,const State& state) {
    return ct.get_id()<=1 || state.reserve || ct.get_unit_count()==1;
}
inline double movement_value(const Controller& ct,const Memory& m,const State& state,
                             const GoalGraph& graph,const std::vector<double>& risk,Candidate& c) {
    const bool queen=ct.get_id()<=1;
    const bool protect=protected_asset(ct,state);
    Position end=c.simulation.body.front();int i=m.index(end);
    c.risk=risk[i]+(c.birth_possible?0.35:0.0);
    double score=(c.food-c.paid)*(protect?130.0:110.0)-15*c.paid;
    if(graph.goal>=0 && graph.field[i]<9999)score+=6.0*(graph.field[m.index(ct.get_position())]-graph.field[i]);
    score-=c.risk*(queen?(750.0+100*ct.get_length()):(protect?240.0+24*ct.get_length():90.0+12*ct.get_length()));
    score-=8*m.visits(end)+std::min(24,m.lifetime_visits(end))*(m.now-state.last_food>=12?2.0:0.5);
    score-=0.4*c.moves.size();
    if(!queen)score-=15*queen_crowding(ct,end);
    if(c.uncertain)score-=protect?180.0:30.0;
    return score;
}
inline bool child_facing(const Controller& ct,const Memory& m,const Simulation& child,Direction& out) {
    if(child.body.size()<2)return false;
    for(auto d:Direction::get_direction_list()) {Position to;
        if(m.destination(ct,child.body[1],d,to)&&to==child.body[0]){out=d;return true;}}
    return false;
}
inline int future_grade(const Future& f,int horizon) {
    if(f.depth>=horizon)return 3;
    // A fully exhausted finite route in the frozen local occupancy model is
    // weaker than an unresolved continuation. Neither proves real survival:
    // observed foreign bodies may move before the next turn.
    if(f.outside||f.portal||f.exhausted)return 2;
    if(f.depth>=2)return 1;
    return 0;
}
inline void assess_investment_terminal(const Controller& ct,const Memory& m,investment::Forecast& f) {
    if(!f.complete)return;
    f.terminal_assessed=true;f.family_max_before=ct.get_length();f.family_max_after=0;
    for(int actor=0;actor<f.world.count;++actor) {
        const auto& a=f.world.actors[actor];
        Simulation s{a.body,f.world.eaten,true,a.length};
        std::vector<Position> blocked;
        for(int other=0;other<f.world.count;++other)if(other!=actor)
            blocked.insert(blocked.end(),f.world.actors[other].body.begin(),f.world.actors[other].body.end());
        // Two steps suffice for this minimum contract. Longer survival and
        // other actors' actual next actions are deliberately not claimed.
        int budget=32;const auto t=continuation(ct,m,s,blocked,0,2,budget);
        f.terminal[actor]={t.depth,future_grade(t,2),t.outside,t.portal,t.exhausted};
        f.family_max_after=std::max(f.family_max_after,a.length);
    }
}
inline int ordinary_investment_rejection(const investment::Forecast& f,bool protected_region,bool rebuild) {
    if(rebuild||!f.complete||!f.terminal_assessed)return 0;
    for(int actor=0;actor<f.world.count;++actor) {
        const auto& t=f.terminal[actor];
        if(t.depth<2&&!t.outside&&!t.portal&&!t.exhausted)return actor+1;
    }
    if(protected_region&&f.family_max_after<f.family_max_before)return 3;
    return 0;
}
inline int contact_tier(const Candidate& c,bool protect,int grade) {
    // Preserve V3's direct visible-head protection. A hypothetical split
    // child is compared only after the continuation evidence grade.
    return protect && grade>=1 && !c.imminent ? 1 : 0;
}
inline bool investment_dominated(const Candidate& split,const Candidate& move,bool protect,int horizon) {
    if(move.kind!=Kind::Move||!move.joint||!move.joint->complete||!split.joint||!split.joint->complete)return false;
    const int sg=future_grade(split.future,horizon),mg=future_grade(move.future,horizon);
    const int sc=contact_tier(split,protect,sg),mc=contact_tier(move,protect,mg);
    const int sb=protect&&!split.birth_possible?1:0,mb=protect&&!move.birth_possible?1:0;
    if(mc<sc||(mc==sc&&(mg<sg||(mg==sg&&mb<sb))))return false;
    // Every compared coordinate belongs to this same admissible MOVE. Never
    // combine the food of one branch with the coverage of another branch.
    return move.joint->food-move.joint->paid>=split.joint->food-split.joint->paid
        &&move.joint->exploration+1e-9>=split.joint->exploration
        &&move.risk<=split.risk+1e-9&&move.joint->world.risk_cost<=split.joint->world.risk_cost+1e-9;
}
// Do not spend a protected scoring asset merely to reduce soft friendly
// reach when a known free route has equally strong continuation and no more
// enemy exposure. Future food remains an estimate, not executed income.
inline bool capital_dominated(const Candidate& paid,const Candidate& free,int horizon) {
    return paid.kind==Kind::Move && paid.paid>paid.food
        && paid.future.next_free_food<paid.paid-paid.food
        && free.kind==Kind::Move && free.paid==0 && !free.uncertain && !free.imminent && !free.birth_possible
        && future_grade(free.future,horizon)>=1
        && future_grade(free.future,horizon)>=future_grade(paid.future,horizon)
        && free.enemy_risk<=paid.enemy_risk+1e-9;
}
inline Direction loss_minimizing_fallback(const Controller& ct,const Memory& m) {
    Direction best=ct.get_dir();double bestLoss=1e30;
    const auto* here=ct.get_tile(ct.get_position());
    for(auto d:Direction::get_direction_list()) {
        Position to;double loss=0;
        if(ct.get_length()>=2&&d==ct.get_dir().get_opposite()) {
            // Incoming direction proves the old neck even for a fresh partial
            // body and a known portal whose reverse exit is outside vision.
            loss=0;
        } else if(!m.destination(ct,ct.get_position(),d,to)) {
            // An unresolved portal is an uncertain escape, not known death.
            if(here&&here->get_edge(d).is_portal()
                && !(ct.get_length()>=2&&d==ct.get_dir().get_opposite()))loss=-100;
        } else if(std::find(m.body.begin(),m.body.end(),to)==m.body.end()) {
            const auto* tile=ct.get_tile(to);
            if(!tile)loss=-100;
            else if(const auto* part=tile->get_dragon()) {
                if(part->is_head()&&part->get_id()!=ct.get_id()) {
                    const int observedLength=static_cast<int>(observed_chain(ct,m,part->get_id()).size());
                    if(part->get_team()==ct.get_team())
                        loss=(part->get_id()<=1?10000.0:1000.0)+50*observedLength;
                    else loss=part->get_id()<=1?-5000.0:-1000.0-20*observedLength;
                }
            } else loss=-100; // Unexpected open cell: retain the possible escape.
        }
        if(loss<bestLoss){best=d;bestLoss=loss;}
    }
    return best;
}
inline Plan choose(const Controller& ct,Memory& m,State& state) {
    update_role(ct,m,state);
    const bool queen=ct.get_id()<=1;
    const bool protect=protected_asset(ct,state);
    std::vector<bool> imminent;
    std::vector<double> enemy_danger;
    const auto danger=risks(ct,m,&imminent,&enemy_danger);const auto graph=goals(ct,m,state);
    const auto births=born_threat::build(ct,m);
#ifndef INVESTMENT_DISABLE_JOINT
    investment::Context joint_context(ct,m);
    joint_context.danger=&danger;joint_context.birth=&births.same_round_possible;
    joint_context.resource_weight=protect?130.0:110.0;
    joint_context.parent_risk_weight=queen?750.0+100*ct.get_length():(protect?240.0+24*ct.get_length():90.0+12*ct.get_length());
    investment::World starting_world;starting_world.actors[0]={m.body,ct.get_length(),ct.get_dir()};
    if(starting_world.actors[0].body.empty())starting_world.actors[0].body.push_back(ct.get_position());
    const double starting_exploration=joint_context.exploration(starting_world);
#endif
    const int free=(ct.get_length()+3)/4,limit=std::min(6,free+2),width=12;
    std::vector<Candidate> candidates,beam;
    Candidate start;start.simulation=initial(ct,m);start.score=0;beam.push_back(start);
    bool alliedQ=friendly_queen(ct);
    const bool trade_ok=!queen && (ct.get_unit_count()>=3 || (ct.get_unit_count()==2 && alliedQ))
        && (!state.reserve||alliedQ);
    for(int depth=0;depth<limit && !beam.empty();++depth) {
        std::vector<Candidate> next_beam;
        for(const auto& parent:beam) for(auto d:Direction::get_direction_list()) {
            if(depth==0&&ct.get_length()>=2&&d==ct.get_dir().get_opposite())continue;
            const bool paid=depth>=free;
            if(paid && parent.simulation.length<=2)continue;
            Position to;const auto* here=ct.get_tile(parent.simulation.body.front());
            if(!here)continue;
            bool resolved=m.destination(ct,parent.simulation.body.front(),d,to);
            if(!resolved) {
                if(depth==0&&here->get_edge(d).is_portal()) {
                    // Even with an unseen portal neck, incoming facing proves
                    // its immediate reverse is occupied by our old body.
                    if(ct.get_length()>=2&&d==ct.get_dir().get_opposite())continue;
                    Candidate c=parent;c.kind=Kind::UnknownPortal;c.moves={d};c.uncertain=true;
                    c.score=(m.now-state.last_food>=12?35.0:0.0)-(protect?220.0:35.0);
                    candidates.push_back(c);
                }
                continue;
            }
            if(!m.cell(to)||std::find(parent.simulation.body.begin(),parent.simulation.body.end(),to)!=parent.simulation.body.end())continue;
            const auto* landing=ct.get_tile(to);const auto* part=landing?landing->get_dragon():nullptr;
            if(part&&part->get_id()!=ct.get_id()) {
                if(trade_ok && part->is_head() && part->get_team()!=ct.get_team() && part->get_id()<=1) {
                    Candidate c=parent;c.kind=Kind::QueenTrade;c.moves.push_back(d);
                    // Fatal target step checks affordability but executes no paid pop.
                    c.score=(alliedQ?2400.0:900.0)-ct.get_length()*(state.reserve?65.0:80.0);
                    c.imminent=false;c.birth_possible=false; // Verified Queen trade is an explicit sacrifice.
                    c.future={8,false,false,false};candidates.push_back(c);
                }
                continue; // Ordinary heads/bodies are never speculative shortcuts.
            }
            if(!landing) {
                // Emit at most the one unknown step, never a guessed follow-up.
                if(!paid && (depth==0 || !protect)) {
                    Candidate c=parent;c.moves.push_back(d);c.uncertain=true;
                    c.simulation.body.push_front(to);
                    if(static_cast<int>(c.simulation.body.size())>c.simulation.length)c.simulation.body.pop_back();
                    c.imminent=imminent[m.index(to)];
                    c.birth_possible=births.same_round_possible[m.index(to)];
                    c.enemy_risk=enemy_danger[m.index(to)];
                    c.score=movement_value(ct,m,state,graph,danger,c);candidates.push_back(c);
                }
                continue;
            }
            Candidate c=parent;if(!step(ct,m,c.simulation,d,paid))continue;
            c.imminent=imminent[m.index(to)];
            c.birth_possible=births.same_round_possible[m.index(to)];
            c.enemy_risk=enemy_danger[m.index(to)];
            c.moves.push_back(d);c.paid+=paid;c.food=static_cast<int>(c.simulation.eaten.size());
            c.score=movement_value(ct,m,state,graph,danger,c);
            candidates.push_back(c);next_beam.push_back(c);
        }
        std::stable_sort(next_beam.begin(),next_beam.end(),[](const Candidate& a,const Candidate& b){return a.score>b.score;});
        if(static_cast<int>(next_beam.size())>width)next_beam.resize(width);
        beam=std::move(next_beam);
    }
    const Simulation original=initial(ct,m);
    const bool rebuild=ct.get_unit_count()==1;
    const bool queen_rebuild=queen&&rebuild&&ct.get_length()>=11;
#ifdef INVESTMENT_DISABLE_JOINT
    const int desired=std::min(ct.unit_limit,std::min(24,std::max(4,graph.food_sites/2+graph.frontiers/6)));
    const bool expand=!queen && ((!state.reserve&&ct.get_length()>=6&&ct.get_unit_count()<desired)
        || (rebuild&&ct.get_length()>=6));
    if(original.complete && (expand||queen_rebuild) && ct.can_split(2)) {
        Candidate c;c.kind=Kind::Split;c.child=2;c.simulation=original;
        c.imminent=imminent[m.index(ct.get_position())];
        c.birth_possible=births.same_round_possible[m.index(ct.get_position())];
        Simulation child;child.length=2;child.complete=true;
        for(int k=0;k<2;++k)child.body.push_back(original.body[original.body.size()-1-k]);
        c.blocked.assign(child.body.begin(),child.body.end());
        c.simulation.length-=2;c.simulation.body.resize(c.simulation.length);
        std::vector<Position> parent_body(c.simulation.body.begin(),c.simulation.body.end());
        Direction facing=ct.get_dir();bool resolvedFacing=child_facing(ct,m,child,facing);
        int exits=0;bool uncertain_child=false;
        if(resolvedFacing)for(auto d:Direction::get_direction_list()) {Position to;
            if(!m.destination(ct,child.body.front(),d,to)||contains(parent_body,to))continue;
            if(!ct.get_tile(to)){uncertain_child=true;continue;}
            Simulation next=child;if(step(ct,m,next,d,false,parent_body))++exits;
        }
        if(resolvedFacing && (exits>0||uncertain_child) && danger[m.index(ct.get_position())]<1.0) {
            c.risk=danger[m.index(ct.get_position())]+danger[m.index(child.body.front())];
            c.uncertain=uncertain_child;
            c.score=(ct.get_unit_count()<3?150.0:20.0+120.0*(desired-ct.get_unit_count())/std::max(1,desired))
                +8*std::min(3,exits)-c.risk*(queen?1100.0:300.0)-(uncertain_child?35.0:0.0)
                -(queen?260.0:(state.reserve?160.0:0.0));
            if(rebuild)c.score+=200;
            candidates.push_back(c);
        }
    }
#else
    // Population is only an official cap/rebuild fact. A personal observation
    // graph cannot veto an otherwise productive regional investment.
    const bool expand=!queen&&ct.get_length()>=6;
    if(original.complete&&(expand||queen_rebuild)&&ct.can_split(2)) {
        auto forecast=investment::evaluate_split(ct,m,original,2,joint_context,320);
        if(forecast.valid&&forecast.complete) {
            investment::World split;
            if(investment::split_world(ct,m,original,2,split)) {
                Candidate c;c.kind=Kind::Split;c.child=2;c.ordinary_investment=true;
                c.simulation={split.actors[0].body,{},true,split.actors[0].length};
                c.blocked.assign(split.actors[1].body.begin(),split.actors[1].body.end());
                c.imminent=imminent[m.index(ct.get_position())];
                c.birth_possible=births.same_round_possible[m.index(ct.get_position())];
                c.risk=danger[m.index(ct.get_position())];c.enemy_risk=enemy_danger[m.index(ct.get_position())];
                c.score=-20.0-c.risk*joint_context.parent_risk_weight-(queen?260.0:(state.reserve?260.0:0.0));
                if(rebuild)c.score+=200;
                c.joint=std::move(forecast);candidates.push_back(std::move(c));
            }
        }
    }
#endif
    // Emergency rescue remains available, including incomplete starting bodies.
    const int emergency=emergency_split_size(ct);
    if(emergency>0) {
        Candidate c;c.kind=Kind::Split;c.child=emergency;c.simulation=original;
        c.imminent=imminent[m.index(ct.get_position())];
        c.birth_possible=births.same_round_possible[m.index(ct.get_position())];
        c.simulation.length=ct.get_length()-emergency;
        if(c.simulation.complete) {
            c.blocked.assign(c.simulation.body.begin()+c.simulation.length,c.simulation.body.end());
            c.simulation.body.resize(c.simulation.length);
        }
        c.uncertain=!original.complete;
        c.score=-100.0-(queen?100.0*ct.get_length():(protect?15.0*ct.get_length():0.0));
        // Complete parent/child bodies permit actual continuation search.
        // Only genuinely partial starting bodies retain unresolved evidence.
        if(c.uncertain)c.future={0,true,false,false};
        candidates.push_back(c);
    }
    std::stable_sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b){return a.score>b.score;});
    std::vector<int> selected;
    for(int i=0;i<std::min(8,static_cast<int>(candidates.size()));++i)selected.push_back(i);
    // Keep the cheapest first-direction alternatives before continuation pruning.
    for(auto d:Direction::get_direction_list()) for(int i=0;i<static_cast<int>(candidates.size());++i)
        if(candidates[i].kind==Kind::Move && candidates[i].moves.size()==1&&candidates[i].moves.front()==d) {
            if(std::find(selected.begin(),selected.end(),i)==selected.end())selected.push_back(i);break;
        }
    // Score the proposal on the same two-round horizon before pruning it.
    for(int i=0;i<static_cast<int>(candidates.size());++i)if(candidates[i].ordinary_investment
        &&std::find(selected.begin(),selected.end(),i)==selected.end())selected.push_back(i);
    const int horizon=queen?8:6;
    for(int i:selected) {
        auto& c=candidates[i];
        if(c.kind!=Kind::QueenTrade && !c.uncertain) {
            int budget=queen?140:90;c.future=continuation(ct,m,c.simulation,c.blocked,0,horizon,budget);
        } else if(c.uncertain && c.future.depth==0) c.future.outside=true;
#ifndef INVESTMENT_DISABLE_JOINT
        if(c.kind==Kind::Move&&!c.uncertain&&c.simulation.complete)
            c.joint=investment::evaluate_move(ct,m,c.simulation,c.moves,c.paid,joint_context,96);
        if(c.joint&&c.joint->complete)assess_investment_terminal(ct,m,*c.joint);
        if(c.ordinary_investment&&c.joint)
            c.investment_rejection=ordinary_investment_rejection(*c.joint,state.reserve,rebuild);
#endif
    }
    int rejected_terminal=0,rejected_capital=0;const Candidate* rejected_proposal=nullptr;
    for(int i:selected)if(candidates[i].investment_rejection) {
        rejected_proposal=&candidates[i];
        if(candidates[i].investment_rejection==3)++rejected_capital;else ++rejected_terminal;
    }
    int best=-1,bestGrade=-1,bestContact=-1,bestBirth=-1;double bestScore=-1e30;
    for(int i:selected) {
        auto& c=candidates[i];
#ifndef INVESTMENT_DISABLE_JOINT
        if(c.investment_rejection)continue;
        bool redundant=false;
        if(c.ordinary_investment&&!rebuild)for(int j:selected)if(i!=j
            &&investment_dominated(c,candidates[j],protect,horizon)){redundant=true;break;}
        if(redundant)continue;
#endif
        bool dominated=false;
        if(protect)for(int j:selected)if(j!=i&&capital_dominated(c,candidates[j],horizon)){dominated=true;break;}
        if(dominated)continue;
        int grade=c.kind==Kind::QueenTrade?3:future_grade(c.future,horizon);
        const int contact=contact_tier(c,protect,grade);
        const int birth=protect&&!c.birth_possible?1:0;
        double score=c.score;
        // A bounded, visible next-turn food opportunity is an estimate. It can
        // justify food-neutral acceleration, without inventing current income.
#ifdef INVESTMENT_DISABLE_JOINT
        score+=45*c.future.next_free_food;
#else
        if(c.joint&&c.joint->complete) {
            const auto& f=*c.joint;
            score+=joint_context.resource_weight*((f.food-f.paid)-(c.food-c.paid))
                -15*(f.paid-c.paid)-f.world.risk_cost+3*(f.exploration-starting_exploration);
        } else score+=45*c.future.next_free_food;
#endif
        if(c.future.exhausted)score-=15;
        if(c.future.depth<horizon)score-=12*(horizon-c.future.depth);
        // Short known continuation and unknown/budget exhaustion are not aliases.
        if(best<0||contact>bestContact||(contact==bestContact &&
           (grade>bestGrade||(grade==bestGrade&&
           (birth>bestBirth||(birth==bestBirth&&score>bestScore)))))) {
            best=i;bestGrade=grade;bestScore=score;bestContact=contact;bestBirth=birth;
        }
    }
    if(best>=0) {
        auto& c=candidates[best];
        if(c.food>0)state.last_food=m.now;
        const std::string kind=c.kind==Kind::Split?"SPLIT":(c.kind==Kind::QueenTrade?"QUEEN_TRADE":(c.kind==Kind::UnknownPortal?"PORTAL":"MOVE"));
        std::string note="GENERALIST "+kind+" role="+(queen?"Q":(ct.get_unit_count()==1?"LAST":(state.reserve?"RESERVE":"HARVEST")))
            +" food="+std::to_string(c.food)+" paid="+std::to_string(c.paid)
            +" depth="+std::to_string(c.future.depth)+" outside="+std::to_string(c.future.outside)
            +" portal="+std::to_string(c.future.portal)+" budget="+std::to_string(c.future.exhausted)
            +" direct_contact="+std::to_string(c.imminent)
            +" possible_birth_contact="+std::to_string(c.birth_possible)
            +" next_food_est="+std::to_string(c.future.next_free_food)
            +" goal="+std::to_string(graph.goal);
        if(c.joint)note+=" joint_food_est="+std::to_string(c.joint->food)
            +" joint_paid_est="+std::to_string(c.joint->paid)+" joint_complete="+std::to_string(c.joint->complete)
            +" joint_unknown="+std::to_string(c.joint->unknown)+" joint_budget="+std::to_string(c.joint->exhausted)
            +" joint_pruned="+std::to_string(c.joint->pruned)
            +" joint_nodes="+std::to_string(c.joint->nodes)+" explore_est="+std::to_string(c.joint->exploration);
        if(c.joint&&c.joint->terminal_assessed)note+=" terminal_parent_depth="+std::to_string(c.joint->terminal[0].depth)
            +" terminal_parent_grade="+std::to_string(c.joint->terminal[0].grade)
            +" terminal_child_depth="+std::to_string(c.joint->world.count==2?c.joint->terminal[1].depth:-1)
            +" terminal_child_grade="+std::to_string(c.joint->world.count==2?c.joint->terminal[1].grade:-1)
            +" family_max_before="+std::to_string(c.joint->family_max_before)
            +" family_max_after="+std::to_string(c.joint->family_max_after);
        note+=" investment_reject_terminal="+std::to_string(rejected_terminal)
            +" investment_reject_capital="+std::to_string(rejected_capital);
        if(rejected_proposal&&rejected_proposal->joint) {
            const auto& f=*rejected_proposal->joint;
            note+=" investment_reject_reason="+std::to_string(rejected_proposal->investment_rejection)
                +" rejected_parent_grade="+std::to_string(f.terminal[0].grade)
                +" rejected_child_grade="+std::to_string(f.terminal[1].grade)
                +" rejected_family_max_before="+std::to_string(f.family_max_before)
                +" rejected_family_max_after="+std::to_string(f.family_max_after);
        }
        note+=" regional_winner="+std::to_string(state.region.visible_winner);
        return {{c.moves.empty()?ct.get_dir():c.moves.front(),c.child},c.moves,note,c.kind,c.food,c.paid,c.uncertain};
    }
    // No modeled survival: minimize additional team score loss. A solo death
    // is preferable to killing the friendly Queen/another scoring reserve.
    const auto fallback=loss_minimizing_fallback(ct,m);
    return {{fallback,0},{fallback},"GENERALIST FALLBACK loss_min no_confirmed_escape",Kind::Fallback,0,0};
}
inline void reconcile_pending(const Controller& ct,Memory& memory,State& state) {
    auto& p=state.pending;
    if(!p.active)return;
    bool valid=ct.get_length()>=p.minimum_length && ct.get_length()<=p.maximum_length
        && (!p.expected_head_known||ct.get_position()==p.expected_head);
    auto body=p.prefix_history;
    body.push_front(ct.get_position());
    while(static_cast<int>(body.size())>ct.get_length())body.pop_back();
    for(std::size_t i=0;i<body.size()&&valid;++i) {
        if(std::find(body.begin()+i+1,body.end(),body[i])!=body.end())valid=false;
        if(const auto* tile=ct.get_tile(body[i])) {
            const auto* part=tile->get_dragon();
            if(!part||part->get_id()!=ct.get_id())valid=false;
        }
    }
    // The real head and length resolve the final step's unknown food/tail.
    // A still-short prefix stays partial; no unseen segments are invented.
    if(valid)memory.body=std::move(body);else memory.body.clear();
    p=PendingBody{};
}
inline void observe(const Controller& ct,Memory& memory,State& state) {
    reconcile_pending(ct,memory,state);
    memory.observe(ct);
}
inline void remember(const Controller& ct,Memory& memory,State& state,const Plan& plan,int round) {
    if(plan.action.child_size==0 && plan.uncertain && !plan.moves.empty()) {
        PendingBody p;p.active=true;p.prefix_history=memory.body;
        if(p.prefix_history.empty())p.prefix_history.push_back(ct.get_position());
        Simulation simulated=initial(ct,memory);
        const int free=(ct.get_length()+3)/4;
        bool valid=true;
        for(std::size_t i=0;i<plan.moves.size();++i) {
            const bool last=i+1==plan.moves.size(),paid=static_cast<int>(i)>=free;
            Position to;
            bool resolved=memory.destination(ct,simulated.body.front(),plan.moves[i],to);
            if(last) {
                if(paid&&simulated.length<=2){valid=false;break;}
                p.expected_head_known=resolved;
                if(resolved)p.expected_head=to;
                p.minimum_length=simulated.length-(paid?1:0);
                p.maximum_length=p.minimum_length+1;
            } else {
                if(!resolved||!step(ct,memory,simulated,plan.moves[i],paid)){valid=false;break;}
                // Keep the whole known history until real final length chooses
                // its tail. Unknown food must not prematurely discard old tail.
                p.prefix_history.push_front(to);
            }
        }
        if(valid)state.pending=std::move(p);
        else {state.pending=PendingBody{};memory.body.clear();}
        return;
    }
    state.pending=PendingBody{};
    remember_action(ct,memory,plan.action,plan.moves,round);
}
} // namespace planner
