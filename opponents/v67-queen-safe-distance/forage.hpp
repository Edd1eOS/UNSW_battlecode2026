#pragma once
#include "strategy.hpp"
#include <cmath>
#include "terrain.hpp"

// v6：先选择有收益的目的地，再在可见区域内规划本回合的安全动作。
// 所有记忆都来自自身视野；没有读取地图文件或对手隐藏状态。
namespace forage {
using namespace strategy;
struct State {
    int goal = -1;
    int goal_since = -1000;
    int last_growth = 0;
    int old_length = 0;
    int last_portal_round = -1000;
    bool collector = false;
};
struct Plan { Decision action; std::vector<Direction> moves; std::string note; };

// 工兵看到敌方 Queen，且一回合内有完整可见通路时，可以交换掉 Queen。
// 路径不穿越其他身体，长度预算以回合开始长度计算；从不让己方 Queen 执行。
inline std::vector<Direction> attack_queen(const Controller& ct,const Memory& m, bool ordinary=false) {
    if(ct.get_id()<=1 || ct.get_unit_count()<3) return {};
    Position target; bool found=false;int best_value=0;
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon();
        if(!p || !p->is_head() || p->get_team()==ct.get_team()) continue;
        int value=p->get_id()<=1?1000:0;
        if(ordinary && ct.get_length()<=4 && p->get_id()>1) {
            int seen=0;
            for(const auto& body:ct.get_tiles())
                if(body.get_dragon() && body.get_dragon()->get_id()==p->get_id()) ++seen;
            if(seen>=ct.get_length()+(ct.get_unit_count()>=10?0:3)) value=seen;
        }
        if(value>best_value) {target=t.get_position();found=true;best_value=value;}
    }
    if(!found) return {};
    const int limit=std::min(10,(ct.get_length()+3)/4+ct.get_length()-2);
    std::vector<int> prev(m.cells.size(),-1), steps(m.cells.size(),0), dirs(m.cells.size(),0);
    std::queue<Position> q; q.push(ct.get_position());prev[m.index(ct.get_position())]=m.index(ct.get_position());
    while(!q.empty()) {
        auto p=q.front();q.pop();if(steps[m.index(p)]>=limit) continue;
        for(auto d:Direction::get_direction_list()) {
            Position n; if(!m.destination(ct,p,d,n)||!m.cell(n)||prev[m.index(n)]>=0) continue;
            const auto* t=ct.get_tile(n); if(!t || (t->get_dragon() && n!=target)) continue;
            prev[m.index(n)]=m.index(p);dirs[m.index(n)]=Atlas::direction_index(d);
            steps[m.index(n)]=steps[m.index(p)]+1;
            if(n==target) {
                std::vector<Direction> path;
                for(int i=m.index(n);i!=m.index(ct.get_position());i=prev[i])
                    path.push_back(Direction::get_direction_list()[dirs[i]]);
                std::reverse(path.begin(),path.end());return path;
            }
            q.push(n);
        }
    }
    return {};
}

inline Position position(const Memory& m, int i) { return {i % m.width, i / m.width}; }
inline int distance(const Memory& m, Position a, Position b) {
    int x=std::abs(a.x-b.x), y=std::abs(a.y-b.y);
    return std::min(x,m.width-x)+std::min(y,m.height-y);
}
// 当前身体是障碍。goal field 可忽略自己的身体，作为未来路线的软估计；
// 真正输出的动作仍逐步模拟身体，不能穿过自己的尾巴。
inline std::vector<int> distances(const Controller& ct, const Memory& m, Position start,
                                  bool ignore_own=false) {
    std::vector<int> dist(m.cells.size(),9999);
    if(!m.cell(start)) return dist;
    std::queue<Position> q; q.push(start); dist[m.index(start)]=0;
    // 探索目标本身没有地形记录，要从已知侧的边反向连回去。
    // 否则以未知格为终点建立距离场时，整张距离场会保持不可达。
    if(!m.cell(start)->known) {
        for(auto d:Direction::get_direction_list()) {
            auto n=start.add_dir(d); Position back;
            for(auto r:Direction::get_direction_list()) {
                if(!m.destination(ct,n,r,back) || back!=start) continue;
                const auto* t=ct.get_tile(n);const auto* part=t?t->get_dragon():nullptr;
                if(part && !(ignore_own && part->get_id()==ct.get_id())) continue;
                if(dist[m.index(n)]!=9999) continue;
                dist[m.index(n)]=1;q.push(n);
            }
        }
    }
    while(!q.empty()) {
        auto p=q.front(); q.pop();
        if(dist[m.index(p)]>=60) continue;
        for(auto d:Direction::get_direction_list()) {
            Position n; if(!m.destination(ct,p,d,n) || !m.cell(n)) continue;
            if(dist[m.index(n)]!=9999) continue;
            const auto* t=ct.get_tile(n); const auto* body=t?t->get_dragon():nullptr;
            if(body && !(ignore_own && body->get_id()==ct.get_id())) continue;
            dist[m.index(n)]=dist[m.index(p)]+1;
            if(m.cells[m.index(n)].known) q.push(n);
        }
    }
    return dist;
}

// Estimate enemy sprint reach using only the visible body chain.
inline int enemy_reach(const Controller& ct,const Memory& m,const unswbc::Tile& head) {
    const auto id=head.get_dragon()->get_id();
    std::vector<Position> chain{head.get_position()}; bool complete=false;
    for(int step=0;step<64;++step) {
        bool added=false;
        for(const auto& t:ct.get_tiles()) {
            const auto* p=t.get_dragon(); Position n;
            if(!p || p->get_id()!=id || p->is_head()
               || std::find(chain.begin(),chain.end(),t.get_position())!=chain.end()) continue;
            if(m.destination(ct,t.get_position(),p->get_dir(),n) && n==chain.back()) {
                chain.push_back(t.get_position()); added=true; break;
            }
        }
        if(added) continue;
        complete=true;
        const auto* tail=ct.get_tile(chain.back());
        for(auto d:Direction::get_direction_list()) {
            Position n;
            if(tail->get_edge(d).get_edge_type()==EdgeType::KELP) continue;
            if(!m.destination(ct,chain.back(),d,n) || !ct.get_tile(n)) complete=false;
        }
        break;
    }
    int length=static_cast<int>(chain.size());
    return std::min(8,complete?std::max(1,(length+3)/4+length-2):std::max(3,(length+3)/4+length-2));
}

inline std::vector<double> queen_danger(const Controller& ct,const Memory& m) {
    std::vector<double> danger(m.cells.size(),0);
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon();
        if(!p || !p->is_head() || p->get_id()==ct.get_id()) continue;
        bool enemy=p->get_team()!=ct.get_team();
        if(!enemy && p->get_id()<ct.get_id()) continue;
        int range=enemy?enemy_reach(ct,m,t):1;
        std::queue<Position> q;std::vector<int> dist(m.cells.size(),-1);
        q.push(t.get_position());dist[m.index(t.get_position())]=0;
        while(!q.empty()) {
            auto at=q.front();q.pop();int depth=dist[m.index(at)];
            if(depth>=range) continue;
            for(auto d:Direction::get_direction_list()) {
                Position n;if(!m.destination(ct,at,d,n)||!m.cell(n)||dist[m.index(n)]>=0) continue;
                const auto* live=ct.get_tile(n);
                if(!live || (live->get_dragon() && live->get_dragon()->get_id()!=ct.get_id())) continue;
                dist[m.index(n)]=depth+1;q.push(n);
                danger[m.index(n)]+=enemy?(depth==0?1.0:(depth==1?0.8:0.6)):0.25;
            }
        }
    }
    return danger;
}

inline std::vector<double> danger_map(const Controller& ct,const Memory& m) {
    std::vector<double> danger(m.cells.size(),0);
    for(const auto& t:ct.get_tiles()) {
        auto p=t.get_dragon();
        if(!p || !p->is_head() || p->get_id()==ct.get_id()) continue;
        if(p->get_team()==ct.get_team() && p->get_id()<ct.get_id()) continue;
        // 后行动的敌人可能使用多步移动；同队也需要给头部留出一步余量。
        int range=p->get_team()==ct.get_team()?1:enemy_reach(ct,m,t);
        std::queue<Position> q; std::vector<int> dist(m.cells.size(),-1);
        q.push(t.get_position()); dist[m.index(t.get_position())]=0;
        while(!q.empty()) {
            auto at=q.front();q.pop(); int depth=dist[m.index(at)];
            if(depth==range) continue;
            for(auto d:Direction::get_direction_list()) {
                Position n; if(!m.destination(ct,at,d,n) || !m.cell(n)) continue;
                const auto* live=ct.get_tile(n); if(!live || live->get_dragon()) continue;
                if(dist[m.index(n)]>=0) continue;
                dist[m.index(n)]=depth+1;
                danger[m.index(n)]+=depth==0?1.0:(depth==1?0.25:0.08/(depth-1));
                q.push(n);
            }
        }
    }
    return danger;
}

inline int select_goal(const Controller& ct, const Memory& m, State& state, const terrain::EscapeMap* exits=nullptr) {
    auto reach=distances(ct,m,ct.get_position());
    double best=-1; int goal=-1;
    std::vector<double> food(m.cells.size(),0);
    for(int i=0;i<static_cast<int>(m.cells.size());++i) {
        auto p=position(m,i); const auto& c=m.cells[i];
        if(!c.known) continue;
        const auto* t=ct.get_tile(p);
        if(t && t->get_dragon()) continue;
        if(c.pearl && m.now-c.seen<=12) food[i]=t?1.0:0.45;
        else if(c.spawn_round>=m.now && c.spawn_round<=m.now+8)
            food[i]=0.25/(1.0+std::max(0,c.spawn_round-m.now-reach[i]));
    }
    for(int i=0;i<static_cast<int>(m.cells.size());++i) {
        if(reach[i]==9999 || reach[i]==0) continue;
        if(exits && exits->worsens(m,ct.get_position(),position(m,i))) continue;
        auto p=position(m,i); const auto& c=m.cells[i];
        double reward=0;
        if(food[i]>0) {
            // 相邻资源只提供额外吸引力；实际路径仍由地形 BFS 决定。
            double cluster=0;
            for(int j=0;j<static_cast<int>(food.size());++j)
                if(food[j]>0 && reach[j]!=9999 && distance(m,p,position(m,j))<=4)
                    cluster+=food[j]/(1.0+distance(m,p,position(m,j)));
            reward=100*food[i]+28*std::min(cluster,5.0);
        } else if(!c.known) reward=20;
        else continue;
        double score=reward/(reach[i]+3.0);
        score/=1.0+0.2*queen_crowding(ct,p);
        if(!c.known) score/=1.0+0.15*m.lifetime_visits(p);
        if(i==state.goal && m.now-state.goal_since<12) score*=1.18;
        if(score>best) { best=score; goal=i; }
    }
    if(goal!=state.goal) { state.goal=goal;state.goal_since=m.now; }
    return goal;
}

inline Plan choose(const Controller& ct, Memory& m, State& state) {
    if(ct.get_length()>state.old_length) state.last_growth=m.now;
    state.old_length=ct.get_length();
    const bool queen=ct.get_id()<=1;
    if(!queen && ct.get_id()%4==2 && m.now>=70 && ct.get_unit_count()>=8) state.collector=true;
    const auto danger=queen?queen_danger(ct,m):danger_map(ct,m);
    const auto exits=terrain::build(ct,m);
    if(!queen) {
        auto attack=attack_queen(ct,m);
        if(!attack.empty()) return {{attack.front(),0},attack,"V7 ATTACK_QUEEN"};
        attack=attack_queen(ct,m,true);
        if(!attack.empty()) return {{attack.front(),0},attack,"V17 ATTACK_LARGE_WORKER"};
    }
    const int goal=select_goal(ct,m,state,&exits);
    const auto field=goal>=0?distances(ct,m,position(m,goal),true):std::vector<int>(m.cells.size(),0);
    Plan plan{{choose_move(ct,m),0},{},""};
    double best=-1e30; int explored=0; int best_viable=-1;
    Simulation initial{m.body,{},static_cast<int>(m.body.size())==ct.get_length(),ct.get_length()};
    if(initial.body.empty()) initial.body.push_back(ct.get_position());
    std::vector<Direction> path;
    // 最多四步，全为回合开始长度所允许的免费动作，不靠吃珍珠增加免费额度。
    const int free_steps=(ct.get_length()+3)/4;
    const int limit=queen?std::min(6,free_steps+2):std::min(4,free_steps);
    auto visit=[&](auto&& self,const Simulation& current)->void {
        if(static_cast<int>(path.size())>=limit || explored>=180) return;
        for(auto d:Direction::get_direction_list()) {
            const bool paid=static_cast<int>(path.size())>=free_steps;
            if(paid && current.length<=2) continue;
            Simulation next=current;
            if(!simulate_step(ct,next,d,&m)) continue;
            if(exits.worsens(m,current.body.front(),next.body.front())) continue;
            if(paid) {--next.length;if(static_cast<int>(next.body.size())>next.length) next.body.pop_back();}
            ++explored; path.push_back(d);
            auto end=next.body.front();
            const int horizon=queen?8:6;
            int budget=queen?220:110; auto future=search_survival(ct,next,0,horizon,budget,&m);
            const int viable=future.depth>=horizon || future.uncertain;
            int safety=future.depth>=6?2:((future.uncertain && future.depth>=2)?2:0);
            auto e=evaluate(ct,end,&m);
            double score=static_cast<int>(next.eaten.size())*(queen || state.collector?175.0:(ct.get_length()==3?230.0:(ct.get_length()==2?150.0:105.0)));
            score-=goal>=0?12.0*std::min(field[m.index(end)],100):0;
            score-=danger[m.index(end)]*(queen?1800.0:(state.collector?300.0:(ct.get_length()<=2?75.0:(ct.get_length()==3?120.0:170.0))));
            score-=10*m.visits(end)+std::min(20,m.lifetime_visits(end))*1.5;
            score+=std::min(e.space,25)*1.2;
            score-=65*queen_crowding(ct,end);
            if(e.frontier_distance>=1000) score-=12*std::max(0,std::min(ct.get_length(),15)-e.space);
            if(!safety) score-=1200+150*(6-future.depth);
            score-=0.4*path.size()+150.0*std::max(0,static_cast<int>(path.size())-free_steps);
            if(viable>best_viable || (viable==best_viable && score>best)) {best_viable=viable;best=score;plan.moves=path;plan.action.direction=path.front();}
            self(self,next); path.pop_back();
        }
    };
    visit(visit,initial);
    if(plan.moves.empty()) plan.moves={plan.action.direction};
    // A known portal may lead outside current vision. The strict visible-path simulator
    // must not silently veto every portal shortcut that the map planner selected.
    // Only short scouts take this uncertainty; Queen and long scoring dragons do not.
    if(!queen && goal>=0 && ct.get_length()<=6 && m.now-state.last_portal_round>=3) {
        const auto* here=ct.get_tile(ct.get_position());
        for(auto d:Direction::get_direction_list()) {
            Position out;
            if(!here->get_edge(d).is_portal() || !m.destination(ct,ct.get_position(),d,out)
               || !m.cell(out) || ct.get_tile(out)) continue;
            if(field[m.index(out)]+1>field[m.index(ct.get_position())]) continue;
            if(exits.worsens(m,ct.get_position(),out)) continue;
            const auto& c=*m.cell(out);
            double score=7.0-12.0*std::min(field[m.index(out)],100)-10*m.visits(out)
                -1.5*std::min(20,m.lifetime_visits(out));
            if(c.pearl && m.now-c.seen<=12) score+=60;
            if(score>best) {
                state.last_portal_round=m.now;
                return {{d,0},{d},"V27 PORTAL_SCOUT goal="+std::to_string(goal)};
            }
        }
    }
    // 先保留可靠的紧急救援，再加上工兵的正常扩张。
    auto rescue=choose_action(ct,m,m.now,false);
    if(rescue.child_size) {plan.action=rescue;plan.moves.clear();return plan;}
    int child=0;
    if(ct.can_split(2) && static_cast<int>(m.body.size())==ct.get_length()
       && nearby_threats(ct,ct.get_position())==0) {
        auto tail=m.body.back(); int tail_space=0;
        for(auto d:Direction::get_direction_list()) {
            Position n; if(!m.destination(ct,tail,d,n)) continue;
            const auto* t=ct.get_tile(n); if(!t || t->get_dragon() || danger[m.index(n)]>=1) continue;
            tail_space=std::max(tail_space,evaluate(ct,n,&m).space);
        }
        const int cap=m.now<280?96:(m.now<400?48:16);
        if(!queen && (!state.collector || ct.get_unit_count()<6) && ct.get_length()>=(m.now<220 || ct.get_unit_count()<10?4:7) && ct.get_unit_count()<cap
           && m.now-m.last_split_round>=1 && m.now<400 && tail_space>=1 && best>-900
           && queen_crowding(ct,tail)<=1)
            child=ct.get_length()/2;
        if(queen && ct.get_unit_count()<2 && ct.get_length()>=11 && m.now<150
           && tail_space>=10 && best>-900) child=3;
    }
    if(child && ct.can_split(child)) {plan.action.child_size=child;plan.moves.clear();}
    plan.note=(queen?"V62 QUEEN goal=":(state.collector?"V62 COLLECTOR goal=":"V62 WORKER goal="))+std::to_string(goal)+" idle="+std::to_string(m.now-state.last_growth)
        +" units="+std::to_string(ct.get_unit_count());
    return plan;
}
}
