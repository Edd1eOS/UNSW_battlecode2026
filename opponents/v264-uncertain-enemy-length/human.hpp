#pragma once
#include "strategy.hpp"
#include <tuple>
#include <sstream>

// A fresh policy: choose an intelligible objective, then execute its shortest
// physically legal route. No learned logits or inherited forage score remain.
namespace human {
using namespace strategy;
struct State { int goal=-1; int last_portal=-1000; bool queen_brood_done=false; };
struct Plan { Decision action; std::vector<Direction> moves; std::string note; };
inline Position pos(const Memory& m,int i) { return {i%m.width,i/m.width}; }
struct Map {
    const Controller& ct; const Memory& m;
    std::vector<std::array<int,4>> next;
    std::vector<std::vector<int>> reverse;
    std::vector<bool> blocked;
    Map(const Controller& c,const Memory& a):ct(c),m(a),next(a.cells.size()),reverse(a.cells.size()),blocked(a.cells.size(),false) {
        for(auto& e:next)e.fill(-1);
        for(const auto& t:ct.get_tiles()) if(t.get_dragon()) blocked[m.index(t.get_position())]=true;
        for(int i=0;i<(int)m.cells.size();++i) if(m.cells[i].known) {
            for(auto d:Direction::get_direction_list()) {Position to;
                if(m.destination(ct,pos(m,i),d,to)&&m.cell(to)) {
                    int j=m.index(to);next[i][Atlas::direction_index(d)]=j;reverse[j].push_back(i);
                }
            }
        }
    }
    std::vector<int> from(int source,bool backwards=false,bool ignore_own=false) const {
        std::vector<int> dist(next.size(),9999);std::queue<int> q;dist[source]=0;q.push(source);
        auto add=[&](int n,int depth) {
            if(n<0||dist[n]!=9999) return;
            if(blocked[n]) {const auto* t=ct.get_tile(pos(m,n)); const auto* p=t?t->get_dragon():nullptr;
                if(!ignore_own||!p||p->get_id()!=ct.get_id())return;}
            dist[n]=depth;q.push(n);
        };
        while(!q.empty()) {int at=q.front();q.pop();if(dist[at]>=70)continue;
            if(backwards) {for(int n:reverse[at])add(n,dist[at]+1);}
            else {for(int n:next[at])add(n,dist[at]+1);}
        }
        return dist;
    }
};
// Queen sees explicitly executable one- and two-step enemy routes. Every
// considered square and edge is visible; current bodies stay blockers. The
// observed enemy length is a lower bound; an incompletely observed short
// chain conservatively allows a third segment. This is a local uncertainty,
// not a claim that the hidden body length has been measured.
inline std::vector<int> contact(const Controller& ct,const Memory& m,const Map& map) {
    std::vector<int> risk(m.cells.size(),0);int our_head=m.index(ct.get_position());
    for(const auto& t:ct.get_tiles()) {const auto* p=t.get_dragon();
        if(!p||!p->is_head()||p->get_id()==ct.get_id())continue;
        bool enemy=p->get_team()!=ct.get_team();
        std::vector<bool> reached(m.cells.size(),false);
        for(int n:map.next[m.index(t.get_position())])if(n>=0&&(!map.blocked[n]||n==our_head)) {
            risk[n]+=enemy?10:1;reached[n]=true;
        }
        if(ct.get_id()>1||!enemy)continue;
        int visible_length=0;for(const auto& segment:ct.get_tiles())
            if(segment.get_dragon()&&segment.get_dragon()->get_id()==p->get_id())++visible_length;
        // Two visible segments do not prove a two-segment enemy. A tail
        // at the vision edge can hide the third segment that funds a sprint.
        // Keep a positively complete length-two chain at its real quota.
        bool complete_short=false;
        if(visible_length==2) {
            const unswbc::Tile* tail=nullptr;
            for(const auto& segment:ct.get_tiles()) {const auto* part=segment.get_dragon();Position toward;
                if(part&&part->get_id()==p->get_id()&&!part->is_head()
                   &&m.destination(ct,segment.get_position(),part->get_dir(),toward)
                   &&toward==t.get_position())tail=&segment;
            }
            if(tail) {
                complete_short=true;
                for(auto direction:Direction::get_direction_list()) {
                    if(tail->get_edge(direction).get_edge_type()==EdgeType::KELP)continue;
                    Position neighbor;
                    if(!m.destination(ct,tail->get_position(),direction,neighbor)||!ct.get_tile(neighbor))complete_short=false;
                }
            }
        }
        if(visible_length<3&&!complete_short)visible_length=3;
        visible_length=std::max(2,visible_length);int free=(visible_length+3)/4;
        for(int first:map.next[m.index(t.get_position())]) {
            if(first<0||map.blocked[first])continue;
            const auto* first_tile=ct.get_tile(pos(m,first));if(!first_tile)continue;
            // A length-two enemy can fund its second step only by first
            // eating a visible pearl. Payability is checked BEFORE step two.
            int after_first=visible_length+(first_tile->has_pearl()?1:0);
            if(free<2&&after_first<=2)continue;
            for(int second:map.next[first]) {
                if(second<0||second==first||reached[second]||!ct.get_tile(pos(m,second)))continue;
                if(map.blocked[second]&&second!=our_head)continue;
                reached[second]=true;risk[second]+=10;
            }
        }
    }
    return risk;
}
inline int tail_exits(const Controller& ct,const Memory& m,const Map& map) {
    if((int)m.body.size()!=ct.get_length())return 0;
    int exits=0;for(int n:map.next[m.index(m.body.back())]) {
        if(n<0)continue;const auto* t=ct.get_tile(pos(m,n));
        if(t&&!t->get_dragon())++exits;
    }return exits;
}
inline std::vector<Direction> kill_queen(const Controller& ct,const Memory& m,const Map& map) {
    if(ct.get_id()<=1||ct.get_unit_count()<2)return {};
    int own_queen=-1;
    for(const auto& t:ct.get_tiles()){const auto* p=t.get_dragon();if(p&&p->is_head()&&p->get_id()<=1&&p->get_team()==ct.get_team())own_queen=m.index(t.get_position());}
    int target=-1,value=-1;for(const auto& t:ct.get_tiles()) {const auto* p=t.get_dragon();
        if(!p||!p->is_head()||p->get_team()==ct.get_team())continue;
        int visible_length=0;for(const auto& segment:ct.get_tiles())if(segment.get_dragon()&&segment.get_dragon()->get_id()==p->get_id())++visible_length;
        int score=p->get_id()<=1?10000:0;
        // A short expendable worker may erase a longer scorer even after
        // both Queens die; the observed enemy length is a lower bound.
        if(score==0&&ct.get_length()<=4&&visible_length>=ct.get_length()+2)score=visible_length-ct.get_length();
        if(score>value&&score>0){value=score;target=m.index(t.get_position());}
    }
    if(target<0)return {};
    int start=m.index(ct.get_position()),limit=std::min(10,(ct.get_length()+3)/4+ct.get_length()-2);
    std::vector<int> prev(map.next.size(),-1),dirs(map.next.size(),0),depth(map.next.size(),0);
    std::queue<int> q;q.push(start);prev[start]=start;
    while(!q.empty()){int at=q.front();q.pop();if(depth[at]>=limit)continue;
        for(int d=0;d<4;++d){int n=map.next[at][d];if(n<0||prev[n]>=0||!ct.get_tile(pos(m,n)))continue;
            if(map.blocked[n]&&n!=target)continue;
            prev[n]=at;dirs[n]=d;depth[n]=depth[at]+1;
            if(n==target){std::vector<Direction> path;for(int k=n;k!=start;k=prev[k])path.push_back(Direction::get_direction_list()[dirs[k]]);
                std::reverse(path.begin(),path.end());return path;}
            q.push(n);
        }
    }return {};
}
inline Plan choose(const Controller& ct,Memory& m,State& state) {
    const bool queen=ct.get_id()<=1;const int start=m.index(ct.get_position());
    Map map(ct,m);auto dist=map.from(start);auto risk=contact(ct,m,map);
    int own_queen=-1,queen_exits_before=0;
    for(const auto& t:ct.get_tiles()){const auto* p=t.get_dragon();if(p&&p->is_head()&&p->get_id()<=1&&p->get_team()==ct.get_team())own_queen=m.index(t.get_position());}
    if(own_queen>=0)for(int n:map.next[own_queen])if(n>=0&&!map.blocked[n])++queen_exits_before;
    auto queen_outlets=[&](const Simulation& simulation){
        if(own_queen<0||queen)return 4;int free=0;
        for(int n:map.next[own_queen]){if(n<0)continue;Position point=pos(m,n);
            if(std::find(simulation.body.begin(),simulation.body.end(),point)!=simulation.body.end())continue;
            const auto* t=ct.get_tile(point);const auto* p=t?t->get_dragon():nullptr;
            if(p&&p->get_id()!=ct.get_id())continue;++free;
        }return free;
    };
    // Preserve the sole visible Queen corridor, not only its first tile.
    // A head's reverse ordinary edge leads to its neck even when that neck
    // lies outside this worker's vision, so it is not a genuine escape.
    std::vector<int> queen_corridor;
    if(own_queen>=0&&!queen) {
        int neck=-1;const auto* qt=ct.get_tile(pos(m,own_queen));
        if(qt&&qt->get_dragon()) {auto back=qt->get_dragon()->get_dir().get_opposite();
            if(qt->get_edge(back).get_edge_type()==EdgeType::EMPTY)neck=m.index(qt->get_position().add_dir(back));}
        int previous=neck,at=own_queen;
        for(int depth=0;depth<3;++depth) {
            std::vector<int> options;
            for(int n:map.next[at]) {
                if(n<0||n==previous||n==own_queen||!ct.get_tile(pos(m,n)))continue;
                if(std::find(queen_corridor.begin(),queen_corridor.end(),n)!=queen_corridor.end())continue;
                const auto* tile=ct.get_tile(pos(m,n));const auto* part=tile->get_dragon();
                if(part&&part->get_id()!=ct.get_id())continue;
                // The first exit must be currently free. Later squares may
                // contain us: moving our whole body out is the point.
                if(depth==0&&part)continue;
                options.push_back(n);
            }
            if(options.size()!=1)break;
            previous=at;at=options.front();queen_corridor.push_back(at);
        }
    }
    auto corridor_blocks=[&](const Simulation& simulation) {
        int blocks=0;for(int i=0;i<(int)queen_corridor.size();++i)
            if(std::find(simulation.body.begin(),simulation.body.end(),pos(m,queen_corridor[i]))!=simulation.body.end())blocks+=3-i;
        return blocks;
    };
    bool occupies_corridor=false;for(int n:queen_corridor)
        if(std::find(m.body.begin(),m.body.end(),pos(m,n))!=m.body.end())occupies_corridor=true;
    bool near_queen=false;if(own_queen>=0&&!queen){auto q=pos(m,own_queen),h=ct.get_position();
        int dx=std::abs(q.x-h.x),dy=std::abs(q.y-h.y);near_queen=std::min(dx,m.width-dx)+std::min(dy,m.height-dy)<=2;}

    int ally_heads=0,free_local=0;
    std::vector<std::vector<int>> ally_distance;
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon();if(!p){++free_local;continue;}
        if(p->is_head()&&p->get_team()==ct.get_team()&&p->get_id()!=ct.get_id()) {
            ++ally_heads;if(ally_distance.size()<4)ally_distance.push_back(map.from(m.index(t.get_position())));
        }
    }
    auto claimed=[&](int target,int own_distance){int count=0;for(const auto& distances:ally_distance)
        if(distances[target]+1<own_distance)++count;return count;};
    auto attack=kill_queen(ct,m,map);if(!attack.empty())return {{attack.front(),0},attack,"V264 VALUE_HEAD_TRADE current_path_affordable positive_visible_segment_exchange_or_enemy_queen"};
    // Reproduction consumes the entire parent's turn; require an actual child
    // exit and a parent continuation. There is no old 8/10-cell space gate.
    const bool queen_brood=queen&&!state.queen_brood_done&&m.now<80&&ct.get_unit_count()<16;
    const bool reserve=!queen&&ct.get_unit_count()>=12&&(ct.get_id()/2)%8==1;
    const bool worker_brood=!queen&&!reserve&&!occupies_corridor&&m.now<150&&!(near_queen&&ct.get_unit_count()>=4);
    if(ct.can_split(2)&&(queen_brood||worker_brood)&&tail_exits(ct,m,map)>0
       && ally_heads<3 && free_local>=8+3*ally_heads) {
        bool parent_exit=false,distinct_exit=false;int tail=m.index(m.body.back());
        int parent_room=0,child_room=0;auto tail_dist=map.from(tail);
        for(const auto& t:ct.get_tiles()){int n=m.index(t.get_position());if(map.blocked[n])continue;
            if(dist[n]>0&&dist[n]<9999)++parent_room;if(tail_dist[n]>0&&tail_dist[n]<9999)++child_room;}

        for(int n:map.next[start])if(n>=0&&!map.blocked[n]) {
            parent_exit=true;for(int k:map.next[tail])if(k>=0&&k!=n&&!map.blocked[k]&&ct.get_tile(pos(m,k)))distinct_exit=true;
        }
        bool enemy_next=queen&&risk[start]>=10;
        if(parent_exit&&distinct_exit&&parent_room>=3&&child_room>=3&&!enemy_next)return {{ct.get_dir(),2},{},"V264 FLOOD length="+std::to_string(ct.get_length())+" units="+std::to_string(ct.get_unit_count())+" distinct_exits=1 local_free="+std::to_string(free_local)};
    }
    int goal=-1;std::tuple<int,int,int,int> goalkey{99999,0,0,0};
    bool food_goal=false;std::string purpose="EXPLORE";
    for(int i=0;i<(int)m.cells.size();++i) {
        if(dist[i]<=0||dist[i]>=9999)continue;const auto& c=m.cells[i];const auto* t=ct.get_tile(pos(m,i));
        if(!c.pearl||(!t&&m.now-c.seen>8))continue;
        int neighbors=0;for(int j:map.next[i])if(j>=0&&m.cells[j].pearl&&m.now-m.cells[j].seen<8)++neighbors;
        auto key=std::make_tuple(dist[i]+(t?0:3)+8*claimed(i,dist[i]),-neighbors,m.lifetime_visits(pos(m,i)),i==state.goal?-1:0);
        if(key<goalkey){goalkey=key;goal=i;food_goal=true;purpose="FOOD";}
    }
    if(goal<0) {
        // Keep productive territory: remembered near-term respawns are a
        // concrete patrol objective, distributed to the closest visible ally.
        for(int i=0;i<(int)m.cells.size();++i){const auto& c=m.cells[i];
            if(dist[i]<=0||dist[i]>=9999||c.spawn_round<m.now||c.spawn_round>m.now+8)continue;
            int eta=std::max(dist[i],c.spawn_round-m.now)+8*claimed(i,dist[i]);
            if(eta>9)continue;auto key=std::make_tuple(eta,0,m.visits(pos(m,i)),i==state.goal?-1:0);
            if(key<goalkey){goalkey=key;goal=i;purpose="PATROL_SPAWN";}
        }
    }
    if(goal<0&&!queen) {
        // Idle workers move onto different open approach squares around a
        // visible enemy, using their ID to distribute attack directions.
        int preferred=(ct.get_id()/2)%4;
        for(const auto& t:ct.get_tiles()){const auto* p=t.get_dragon();
            if(!p||!p->is_head()||p->get_team()==ct.get_team())continue;
            int enemy=m.index(t.get_position());
            for(int d=0;d<4;++d){int n=map.next[enemy][d];if(n<0||dist[n]<=0||dist[n]>=9999||map.blocked[n])continue;
                int priority=(p->get_id()<=1?0:4)+dist[n]+(d==preferred?0:2)+8*claimed(n,dist[n]);
                auto key=std::make_tuple(priority,0,m.visits(pos(m,n)),0);
                if(key<goalkey){goalkey=key;goal=n;purpose="FLANK";}
            }
        }
    }
    if(goal<0) {
        // Go to a specific unexplored boundary; staying in a familiar loop is
        // worse than taking a slightly farther new boundary.
        for(int i=0;i<(int)m.cells.size();++i) {
            if(m.cells[i].known||dist[i]>=9999)continue;
            int approach=0;for(int n:map.reverse[i])approach=std::max(approach,m.lifetime_visits(pos(m,n)));
            auto key=std::make_tuple(dist[i]+std::min(24,approach*3)+8*claimed(i,dist[i]),0,0,i==state.goal?-2:0);
            if(key<goalkey){goalkey=key;goal=i;}
        }
    }
    state.goal=goal;auto field=goal>=0?map.from(goal,true,true):std::vector<int>(m.cells.size(),0);
    Plan plan{{ct.get_dir(),0},{},""};
    using Key=std::tuple<int,int,int,int,int,int,int,int,int,int,int,int>;
    Key best{-999,-999,-999,-999,-999,-999,-999,-999,-999,-999,-999,-999};
    std::array<Key,4> direction_best;direction_best.fill(best);
    std::array<bool,4> direction_ok{};
    const int free=(ct.get_length()+3)/4,limit=std::min(7,free+2);
    Simulation initial{m.body,{},(int)m.body.size()==ct.get_length(),ct.get_length()};
    if(initial.body.empty())initial.body.push_back(ct.get_position());
    std::vector<Direction> path;
    int bestgain=0,bestpaid=0,bestdistance=9999,bestrisk=0,bestdead=0,bestqueenexit=4,bestcorridor=0,bestblind=0;
    auto search=[&](auto&& self,const Simulation& current,int first,int& budget)->void {
        if((int)path.size()>=limit||budget<=0)return;
        auto dirs=Direction::get_direction_list();
        std::stable_sort(dirs.begin(),dirs.end(),[&](Direction a,Direction b){
            int i=map.next[m.index(current.body.front())][Atlas::direction_index(a)];
            int j=map.next[m.index(current.body.front())][Atlas::direction_index(b)];
            return (i>=0?field[i]:99999)<(j>=0?field[j]:99999);});
        for(auto d:dirs) {
            if(path.empty()&&Atlas::direction_index(d)!=first)continue;
            bool paid=(int)path.size()>=free;if(paid&&current.length<=2)continue;
            Simulation next=current;if(!simulate_step(ct,next,d,&m))continue;
            if(paid){--next.length;if((int)next.body.size()>next.length)next.body.pop_back();}
            --budget;path.push_back(d);int end=m.index(next.body.front());
            int cost=std::max(0,(int)path.size()-free),gain=(int)next.eaten.size()-cost;
            // Paid food collection must increase length, never merely convert
            // the pearl into speed. Queen emergency escapes are the exception.
            bool paid_escape=queen&&risk[start]>0&&risk[end]==0;
            if(cost==0||gain>0||paid_escape) {
                int future_budget=30;auto future=search_survival(ct,next,0,3,future_budget,&m);
                bool dead=future.depth<3&&!future.uncertain;
                int nearest=goal>=0?field[end]:0;
                if(food_goal&&std::find(next.eaten.begin(),next.eaten.end(),pos(m,goal))!=next.eaten.end())nearest=0;
                // Queen enemy contact and a local static trap precede food. For
                // workers, danger only breaks equally productive route ties.
                int qout=queen_outlets(next);
                int closes_queen=(!queen&&own_queen>=0&&queen_exits_before>0&&qout==0)?-2:
                    ((!queen&&own_queen>=0&&queen_exits_before>=2&&qout<2)?-1:0);
                // A worker's new body may not seal its Queen's last exit just
                // to collect food. Queen avoids entering friendly head traffic
                // when two moves have the same immediate net food gain.
                int corridor=queen?0:corridor_blocks(next);
                int blind=0;
                if(queen&&future.depth<3&&future.uncertain) {
                    int exits=0;const auto* here=ct.get_tile(next.body.front());
                    for(auto direction:Direction::get_direction_list()) {Position to;
                        if(!m.destination(ct,next.body.front(),direction,to)){
                            if(here&&here->get_edge(direction).is_portal())++exits;continue;}
                        if(!ct.get_tile(to)){++exits;continue;}
                        Simulation continuation=next;if(simulate_step(ct,continuation,direction,&m))++exits;
                    }
                    // A one-way route which reaches the visibility boundary
                    // before three confirmed steps should not masquerade as
                    // a verified continuation. Open exploration stays equal.
                    if(exits<=1)blind=1;
                }
                Key key{dead?-1:0,closes_queen,-corridor,queen?-(risk[end]/10):0,-blind,gain,queen?-(risk[end]%10):0,-std::min(999,nearest),-m.visits(next.body.front()),queen?0:-risk[end],-std::min(30,m.lifetime_visits(next.body.front())),-(int)path.size()};
                if(!direction_ok[first]||key>direction_best[first]){direction_ok[first]=true;direction_best[first]=key;}
                if(plan.moves.empty()||key>best){best=key;plan.moves=path;plan.action.direction=path.front();bestgain=gain;bestpaid=cost;bestdistance=nearest;bestrisk=risk[end];bestdead=dead;bestqueenexit=qout;bestcorridor=corridor;bestblind=blind;}
            }
            self(self,next,first,budget);path.pop_back();if(budget<=0)break;
        }
    };
    for(int d=0;d<4;++d){int budget=55;search(search,initial,d,budget);}
    // A known portal's distant landing is not visible. Permit the shortest
    // route to use it, while marking the occupancy uncertainty explicitly.
    if(!queen&&goal>=0&&m.now-state.last_portal>=3) {
        const auto* here=ct.get_tile(ct.get_position());
        for(auto d:Direction::get_direction_list()){int n=map.next[start][Atlas::direction_index(d)];
            if(n<0||!here->get_edge(d).is_portal()||ct.get_tile(pos(m,n)))continue;
            if(field[n]+1<=field[start]&&bestgain<=0){state.last_portal=m.now;return {{d,0},{d},"V264 PORTAL_ROUTE goal="+std::to_string(goal)+" unseen_occupancy"};}
        }
    }
    // An unresolved portal is a purposeful scout option when local food is
    // absent, rather than endlessly orbiting the same known boundary.
    if(!queen&&!food_goal&&m.now-state.last_portal>=6) {
        const auto* here=ct.get_tile(ct.get_position());
        for(auto d:Direction::get_direction_list())if(here->get_edge(d).is_portal()&&map.next[start][Atlas::direction_index(d)]<0){
            state.last_portal=m.now;return {{d,0},{d},"V264 PORTAL_SCOUT unknown_exit"};}
    }
    if(plan.moves.empty()) {
        // A resolved portal can leave the current 7x7 window. The visible
        // simulator cannot certify that landing, but splitting in a sealed
        // local cell is not a reason to discard this concrete escape route.
        if(queen) {
            const auto* here=ct.get_tile(ct.get_position());
            if(here)for(auto direction:Direction::get_direction_list()) {
                Position landing;
                if(!here->get_edge(direction).is_portal()||!m.destination(ct,ct.get_position(),direction,landing)||!m.cell(landing))continue;
                if(std::find(m.body.begin(),m.body.end(),landing)!=m.body.end())continue;
                const auto* target=ct.get_tile(landing);if(target&&target->get_dragon())continue;
                state.last_portal=m.now;
                return {{direction,0},{direction},"V264 KNOWN_PORTAL_ESCAPE target="+std::to_string(landing.x)+","+std::to_string(landing.y)+" unseen_occupancy="+std::to_string(target?0:1)};
            }
        }
        int split=emergency_split_size(ct);if(split)return {{ct.get_dir(),split},{},"V264 EMERGENCY_TAIL_HANDOFF"};
        auto d=choose_move(ct,m);
        auto friendly_head=[&](Direction dir){int n=map.next[start][Atlas::direction_index(dir)];if(n<0)return false;
            const auto* t=ct.get_tile(pos(m,n));const auto* p=t?t->get_dragon():nullptr;
            return p&&p->is_head()&&p->get_team()==ct.get_team()&&p->get_id()!=ct.get_id();};
        if(friendly_head(d))for(auto alt:Direction::get_direction_list())if(!friendly_head(alt)){d=alt;break;}
        return {{d,0},{d},"V264 FORCED_ESCAPE no_confirmed_legal_route"};
    }
    std::ostringstream note;note<<"V264 "<<purpose<<" target=";
    if(goal>=0)note<<pos(m,goal).x<<","<<pos(m,goal).y;else note<<"none";
    note<<" net="<<bestgain<<" paid="<<bestpaid<<" distance="<<bestdistance<<" enemy_reach="<<(queen?2:1)<<" contact="<<bestrisk<<" trap="<<bestdead<<" queen_exits="<<queen_exits_before<<"->"<<bestqueenexit<<" corridor="<<bestcorridor<<" blind_narrow="<<bestblind<<" options=";
    for(int d=0;d<4;++d){note<<(char)Direction::get_direction_list()[d].value<<":";
        if(!direction_ok[d])note<<"blocked";else note<<"g"<<std::get<5>(direction_best[d])<<"/d"<<-std::get<7>(direction_best[d])<<"/trap"<<-std::get<0>(direction_best[d]);note<<";";}
    plan.note=note.str();return plan;
}
}
