#pragma once
#include "strategy.hpp"
#include "terrain.hpp"
#include <cmath>

// One bounded candidate pipeline. All information comes from this unit's input.
namespace planner {
using namespace strategy;
enum class Kind { Move, Split, QueenTrade, UnknownPortal, Fallback };
struct Future { int depth=0; bool outside=false, portal=false, exhausted=false; int next_free_food=0; };
struct State {
    bool reserve=false;
    int old_length=0, last_food=-1000, goal=-1, goal_since=-1000;
};
struct Candidate {
    Kind kind=Kind::Move;
    Simulation simulation;
    std::vector<Direction> moves;
    std::vector<Position> blocked;
    int child=0, food=0, paid=0;
    bool uncertain=false;
    double score=-1e30, risk=0;
    Future future;
};
struct Plan { Decision action; std::vector<Direction> moves; std::string note; Kind kind; int food=0,paid=0; };

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
                           int initial_food=-1,int next_free=-1) {
    if(initial_food<0)initial_food=static_cast<int>(s.eaten.size());
    if(next_free<0)next_free=(s.length+3)/4;
    const int food=depth<=next_free?static_cast<int>(s.eaten.size())-initial_food:0;
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
        auto f=continuation(ct,m,next,blocked,depth+1,horizon,budget,initial_food,next_free);
        best.depth=std::max(best.depth,f.depth);
        best.outside=best.outside||f.outside;best.portal=best.portal||f.portal;
        best.exhausted=best.exhausted||f.exhausted;
        best.next_free_food=std::max(best.next_free_food,f.next_free_food);
        if(best.depth>=horizon) return best;
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
inline std::vector<double> risks(const Controller& ct,const Memory& m) {
    std::vector<double> risk(m.cells.size(),0);
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
                risk[m.index(to)]+=enemy?(n==0?1.0:(n==1?0.35:0.12/(n-1))):(n==0?0.35:0.08);
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
    if(ct.get_id()>1 && ((ct.get_length()>=8 && ct.get_unit_count()>=3)
        || (m.reserve_worker && m.splits_done>=1))) state.reserve=true;
    // Deliberately no population-based demotion: current capital remains a reserve.
}
inline double movement_value(const Controller& ct,const Memory& m,const State& state,
                             const GoalGraph& graph,const std::vector<double>& risk,Candidate& c) {
    const bool queen=ct.get_id()<=1;
    Position end=c.simulation.body.front();int i=m.index(end);
    c.risk=risk[i];
    double score=(c.food-c.paid)*(queen||state.reserve?130.0:110.0)-15*c.paid;
    if(graph.goal>=0 && graph.field[i]<9999)score+=6.0*(graph.field[m.index(ct.get_position())]-graph.field[i]);
    score-=c.risk*(queen?(750.0+100*ct.get_length()):(state.reserve?240.0+24*ct.get_length():90.0+12*ct.get_length()));
    score-=8*m.visits(end)+std::min(24,m.lifetime_visits(end))*(m.now-state.last_food>=12?2.0:0.5);
    score-=0.4*c.moves.size();
    if(!queen)score-=15*queen_crowding(ct,end);
    if(c.uncertain)score-=queen||state.reserve?180.0:30.0;
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
    if(f.depth>=2)return 2;
    if(f.outside||f.portal||f.exhausted)return 1;
    return 0;
}
inline Plan choose(const Controller& ct,Memory& m,State& state) {
    update_role(ct,m,state);
    const bool queen=ct.get_id()<=1;
    const auto danger=risks(ct,m);const auto graph=goals(ct,m,state);
    const int free=(ct.get_length()+3)/4,limit=std::min(6,free+2),width=12;
    std::vector<Candidate> candidates,beam;
    Candidate start;start.simulation=initial(ct,m);start.score=0;beam.push_back(start);
    bool alliedQ=friendly_queen(ct);
    const bool trade_ok=!queen && (ct.get_unit_count()>=3 || (ct.get_unit_count()==2 && alliedQ))
        && (!state.reserve||alliedQ);
    for(int depth=0;depth<limit && !beam.empty();++depth) {
        std::vector<Candidate> next_beam;
        for(const auto& parent:beam) for(auto d:Direction::get_direction_list()) {
            const bool paid=depth>=free;
            if(paid && parent.simulation.length<=2)continue;
            Position to;const auto* here=ct.get_tile(parent.simulation.body.front());
            if(!here)continue;
            bool resolved=m.destination(ct,parent.simulation.body.front(),d,to);
            if(!resolved) {
                if(depth==0&&here->get_edge(d).is_portal()) {
                    Candidate c=parent;c.kind=Kind::UnknownPortal;c.moves={d};c.uncertain=true;
                    c.score=(m.now-state.last_food>=12?35.0:0.0)-(queen||state.reserve?220.0:35.0);
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
                    c.future={8,false,false,false};candidates.push_back(c);
                }
                continue; // Ordinary heads/bodies are never speculative shortcuts.
            }
            if(!landing) {
                // Emit at most the one unknown step, never a guessed follow-up.
                if(!paid && (depth==0 || (!queen&&!state.reserve))) {
                    Candidate c=parent;c.moves.push_back(d);c.uncertain=true;
                    c.simulation.body.push_front(to);
                    if(static_cast<int>(c.simulation.body.size())>c.simulation.length)c.simulation.body.pop_back();
                    c.score=movement_value(ct,m,state,graph,danger,c);candidates.push_back(c);
                }
                continue;
            }
            Candidate c=parent;if(!step(ct,m,c.simulation,d,paid))continue;
            c.moves.push_back(d);c.paid+=paid;c.food=static_cast<int>(c.simulation.eaten.size());
            c.score=movement_value(ct,m,state,graph,danger,c);
            candidates.push_back(c);next_beam.push_back(c);
        }
        std::stable_sort(next_beam.begin(),next_beam.end(),[](const Candidate& a,const Candidate& b){return a.score>b.score;});
        if(static_cast<int>(next_beam.size())>width)next_beam.resize(width);
        beam=std::move(next_beam);
    }
    const Simulation original=initial(ct,m);
    const int desired=std::min(ct.unit_limit,std::min(24,std::max(4,graph.food_sites/2+graph.frontiers/6)));
    const bool rebuild=ct.get_unit_count()==1;
    const bool expand=!queen && ((!state.reserve&&ct.get_length()>=6&&ct.get_unit_count()<desired)
        || (rebuild&&ct.get_length()>=6));
    const bool queen_rebuild=queen&&rebuild&&ct.get_length()>=11;
    if(original.complete && (expand||queen_rebuild) && ct.can_split(2)) {
        Candidate c;c.kind=Kind::Split;c.child=2;c.simulation=original;
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
    // Emergency rescue remains available, including incomplete starting bodies.
    const int emergency=emergency_split_size(ct);
    if(emergency>0) {
        Candidate c;c.kind=Kind::Split;c.child=emergency;c.simulation=original;
        c.simulation.length=ct.get_length()-emergency;
        if(c.simulation.complete) {
            c.blocked.assign(c.simulation.body.begin()+c.simulation.length,c.simulation.body.end());
            c.simulation.body.resize(c.simulation.length);
        }
        c.uncertain=true;c.score=-100.0-(queen?100.0*ct.get_length():(state.reserve?15.0*ct.get_length():0.0));
        c.future={0,true,false,false};candidates.push_back(c);
    }
    std::stable_sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b){return a.score>b.score;});
    std::vector<int> selected;
    for(int i=0;i<std::min(8,static_cast<int>(candidates.size()));++i)selected.push_back(i);
    // Keep the cheapest first-direction alternatives before continuation pruning.
    for(auto d:Direction::get_direction_list()) for(int i=0;i<static_cast<int>(candidates.size());++i)
        if(candidates[i].kind==Kind::Move && candidates[i].moves.size()==1&&candidates[i].moves.front()==d) {
            if(std::find(selected.begin(),selected.end(),i)==selected.end())selected.push_back(i);break;
        }
    int best=-1,bestGrade=-1;double bestScore=-1e30;
    const int horizon=queen?8:6;
    for(int i:selected) {
        auto& c=candidates[i];
        if(c.kind!=Kind::QueenTrade && !c.uncertain) {
            int budget=queen?140:90;c.future=continuation(ct,m,c.simulation,c.blocked,0,horizon,budget);
        } else if(c.uncertain && c.future.depth==0) c.future.outside=true;
        int grade=c.kind==Kind::QueenTrade?3:future_grade(c.future,horizon);
        double score=c.score;
        // A bounded, visible next-turn food opportunity is an estimate. It can
        // justify food-neutral acceleration, without inventing current income.
        score+=45*c.future.next_free_food;
        if(c.future.exhausted)score-=15;
        if(c.future.depth<horizon)score-=12*(horizon-c.future.depth);
        // Short known continuation and unknown/budget exhaustion are not aliases.
        if(best<0||grade>bestGrade||(grade==bestGrade&&score>bestScore)) {best=i;bestGrade=grade;bestScore=score;}
    }
    if(best>=0) {
        auto& c=candidates[best];
        if(c.food>0)state.last_food=m.now;
        const std::string kind=c.kind==Kind::Split?"SPLIT":(c.kind==Kind::QueenTrade?"QUEEN_TRADE":(c.kind==Kind::UnknownPortal?"PORTAL":"MOVE"));
        std::string note="GENERALIST "+kind+" role="+(queen?"Q":(state.reserve?"RESERVE":"HARVEST"))
            +" food="+std::to_string(c.food)+" paid="+std::to_string(c.paid)
            +" depth="+std::to_string(c.future.depth)+" outside="+std::to_string(c.future.outside)
            +" portal="+std::to_string(c.future.portal)+" budget="+std::to_string(c.future.exhausted)
            +" next_food_est="+std::to_string(c.future.next_free_food)
            +" goal="+std::to_string(graph.goal);
        return {{c.moves.empty()?ct.get_dir():c.moves.front(),c.child},c.moves,note,c.kind,c.food,c.paid};
    }
    // No modeled survival: choose a passable edge before a known wall. No hidden
    // endpoint or forced-collision fallback is advertised as safe.
    const auto* here=ct.get_tile(ct.get_position());
    Direction fallback=ct.get_dir();
    if(here)for(auto d:Direction::get_direction_list())if(here->get_edge(d).is_passable()){fallback=d;break;}
    return {{fallback,0},{fallback},"GENERALIST FALLBACK no_confirmed_escape",Kind::Fallback,0,0};
}
} // namespace planner
