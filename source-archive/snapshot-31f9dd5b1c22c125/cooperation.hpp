#pragma once
#include "strategy.hpp"

namespace cooperation {
using namespace unswbc;
enum class Mode { Harvest, Yield, Approach, AwaitDrop, Collect, Release };
struct Memory {
    Mode mode = Mode::Harvest;
    bool crowded = false;
    int clear_turns = 0;
    int approach_until = -1, retry_after = 0;
    int donor = -1, expires = -1, next_grant = 0;
    bool drop_confirmed = false;
    std::vector<Position> drops;
    int receipt_length = 0, receipt_total = 0, receipt_food = 0;
};
struct Plan {
    strategy::Decision action{Direction::NORTH,0};
    std::vector<Direction> moves;
    std::optional<std::pair<Direction,std::uint64_t>> sonar;
    std::string telemetry;
};
struct Density { int cells=0, allied=0, heads=0; };

inline int distance(Position a, Position b) {
    auto [w,h]=unswbc::game->get_map_size();
    int x=std::abs(a.x-b.x), y=std::abs(a.y-b.y);
    return std::min(x,w-x)+std::min(y,h-y);
}
// 按地形连通区域统计，而不是把墙另一边的龙也算成拥堵。
inline Density density(const Controller& ct) {
    Density out;
    std::vector<Position> seen{ct.get_position()};
    for(std::size_t i=0;i<seen.size();++i) {
        const auto* t=ct.get_tile(seen[i]); if(!t) continue;
        ++out.cells;
        const auto* p=t->get_dragon();
        if(p && p->get_team()==ct.get_team()) { ++out.allied; if(p->is_head()) ++out.heads; }
        for(auto d:Direction::get_direction_list()) {
            if(t->get_edge(d).get_edge_type()!=EdgeType::EMPTY) continue;
            auto n=seen[i].add_dir(d);
            if(ct.get_tile(n) && std::find(seen.begin(),seen.end(),n)==seen.end()) seen.push_back(n);
        }
    }
    return out;
}
inline void update_density(Memory& m, Density d) {
    const bool high=d.heads>=4 || (d.cells>0 && 100*d.allied>=35*d.cells);
    const bool low=d.heads<=2 && d.cells>0 && 100*d.allied<25*d.cells;
    if(high) { m.crowded=true; m.clear_turns=0; }
    else if(m.crowded) {
        m.clear_turns=low ? m.clear_turns+1 : 0;
        if(m.clear_turns>=3) { m.crowded=false; m.clear_turns=0; }
    }
}

inline const DragonPart* head(const Controller& ct, int id) {
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon();
        if(p && p->get_id()==id && p->is_head()) return p;
    }
    return nullptr;
}
inline int queen_id(const Controller& ct) {
    for(int id:{0,1}) { const auto* p=head(ct,id); if(p && p->get_team()==ct.get_team()) return id; }
    return -1;
}
// 从头沿身体指向关系反向还原。尾巴四邻必须可见，禁止传送门和断链。
// 否则“看到了几节”不能当成“整条龙只有几节”。
inline std::deque<Position> complete_body(const Controller& ct,int id) {
    const auto* h=head(ct,id); if(!h) return {};
    std::deque<Position> body{h->get_position()};
    int visible=0;
    for(const auto& t:ct.get_tiles()) if(t.get_dragon() && t.get_dragon()->get_id()==id) ++visible;
    while(true) {
        const auto* tail=ct.get_tile(body.back()); if(!tail) return {};
        std::optional<Position> predecessor;
        for(auto d:Direction::get_direction_list()) {
            const auto& edge=tail->get_edge(d);
            if(edge.is_portal()) return {};
            if(edge.get_edge_type()==EdgeType::KELP) continue;
            const auto* next=ct.get_tile(body.back().add_dir(d));
            if(!next) return {}; // 不知道是否还有身体在视野外。
            const auto* p=next->get_dragon();
            if(!p || p->get_id()!=id || p->is_head()) continue;
            if(next->get_edge(p->get_dir()).get_edge_type()!=EdgeType::EMPTY) return {};
            if(next->get_position().add_dir(p->get_dir())!=body.back()) continue;
            if(predecessor || std::find(body.begin(),body.end(),next->get_position())!=body.end()) return {};
            predecessor=next->get_position();
        }
        if(!predecessor) break;
        body.push_back(*predecessor);
    }
    if(static_cast<int>(body.size())!=visible) return {};
    return body;
}
inline std::vector<Position> drop_cells(const std::deque<Position>& body) {
    std::vector<Position> out;
    for(std::size_t i=0;i<body.size();i+=2) out.push_back(body[i]);
    return out;
}
inline bool contains(const std::vector<Position>& v,Position p) {
    return std::find(v.begin(),v.end(),p)!=v.end();
}
// 交付区域只允许 Queen 和这一条工兵的头；其他身体仍是障碍。
inline bool quiet_site(const Controller& ct,int queen,int donor) {
    for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon(); if(!p) continue;
        if(p->get_team()!=ct.get_team()) return false;
        if(p->is_head() && p->get_id()!=queen && p->get_id()!=donor) return false;
    }
    return true;
}
inline std::optional<Direction> release_direction(const Controller& ct) {
    const auto* t=ct.get_tile(ct.get_position()); if(!t) return {};
    for(auto d:Direction::get_direction_list())
        if(t->get_edge(d).get_edge_type()==EdgeType::KELP) return d;
    for(auto d:Direction::get_direction_list()) {
        if(t->get_edge(d).get_edge_type()!=EdgeType::EMPTY) continue;
        const auto* n=ct.get_tile(ct.get_position().add_dir(d));
        const auto* p=n ? n->get_dragon() : nullptr;
        if(p && p->get_id()==ct.get_id() && !p->is_head()) return d;
    }
    return {}; // 不撞其他龙，也不发送非法指令来制造死亡。
}

// 只用 32 位：初始第一回合尚未完成协议升级，64 位消息会被引擎丢弃。
// 长度和位置必须现场读取，不能相信消息里自报的数据。
struct Grant { int donor,round,queen; };
inline std::uint64_t pack(Grant g) {
    return (std::uint64_t{0x35}<<26) | (std::uint64_t(g.queen)<<25)
        | (std::uint64_t(g.round)<<16) | g.donor;
}
inline std::optional<Grant> unpack(std::uint64_t v) {
    if((v>>26)!=0x35) return {};
    return Grant{int(v&65535),int((v>>16)&511),int((v>>25)&1)};
}
struct Route { std::vector<Direction> moves; int food=0,total=0; };
// 对释放后的真实格子做有界搜索。只走免费步，不穿门，不出当前视野。
inline Route pickup_route(const Controller& queen,const std::deque<Position>& body,
                          const std::vector<Position>& drops,int minimum) {
    Route best;
    if(body.size()!=static_cast<std::size_t>(queen.get_length()) || body.empty()) return best;
    strategy::Memory memory; memory.body=body; memory.observe_map(queen,unswbc::game->get_round_num());
    strategy::Simulation initial{body,{},true,queen.get_length()};
    std::vector<Direction> path;
    const int limit=std::min(3,(queen.get_length()+3)/4);
    auto search=[&](auto&& self,const strategy::Simulation& s)->void {
        if(static_cast<int>(path.size())>=limit) return;
        for(auto d:Direction::get_direction_list()) {
            const auto* from=queen.get_tile(s.body.front());
            if(!from || from->get_edge(d).get_edge_type()!=EdgeType::EMPTY) continue;
            auto next=s;
            if(!strategy::simulate_step(queen,next,d,&memory)) continue;
            path.push_back(d);
            int food=0; for(auto p:next.eaten) if(contains(drops,p)) ++food;
            if(food>=minimum && food>best.food) {
                int budget=192;
                auto future=strategy::search_survival(queen,next,0,6,budget,&memory);
                if(future.depth==6) best={path,food,static_cast<int>(next.eaten.size())};
            }
            self(self,next); path.pop_back();
        }
    };
    search(search,initial);
    return best;
}
inline void remove_donor(Controller& scene,int donor,const std::vector<Position>& drops) {
    for(auto& t:scene.vision.tiles) {
        if(t.get_dragon() && t.get_dragon()->get_id()==donor) t.dragon_part.reset();
        if(contains(drops,t.get_position())) t.pearl=true;
    }
}
inline bool project(Controller& scene,const strategy::Memory& memory,const std::vector<Direction>& moves) {
    if(memory.body.size()!=static_cast<std::size_t>(scene.get_length()) || moves.empty()) return false;
    strategy::Simulation s{memory.body,{},true,scene.get_length()};
    for(auto d:moves) if(!strategy::simulate_step(scene,s,d,&memory)) return false;
    for(auto& t:scene.vision.tiles) if(t.get_dragon() && t.get_dragon()->get_id()==scene.get_id()) t.dragon_part.reset();
    for(std::size_t i=0;i<s.body.size();++i) {
        auto* t=scene.get_tile(s.body[i]); if(!t) return false;
        Direction toward=moves.back();
        if(i) {
            bool adjacent=false;
            for(auto d:Direction::get_direction_list()) if(s.body[i].add_dir(d)==s.body[i-1]) { toward=d; adjacent=true; break; }
            if(!adjacent) return false; // 交付协作暂不跨传送门。
        }
        t->dragon_part=DragonPart{s.body[i],scene.get_id(),scene.get_team(),toward,i==0};
    }
    for(auto p:s.eaten) scene.get_tile(p)->pearl=false;
    scene.head=DragonPart{s.body.front(),scene.get_id(),scene.get_team(),moves.back(),true};
    scene.length=s.length;
    return true;
}
inline std::optional<Direction> sonar_to(const Controller& queen,int donor) {
    for(auto d:Direction::get_direction_list()) {
        if(d==queen.get_dir().get_opposite()) continue; // 避开从尾巴发出的特殊声呐。
        auto p=queen.get_position();
        for(int n=0;n<6;++n) {
            const auto* t=queen.get_tile(p);
            if(!t || t->get_edge(d).get_edge_type()!=EdgeType::EMPTY) break;
            p=p.add_dir(d); const auto* next=queen.get_tile(p); if(!next) break;
            const auto* part=next->get_dragon();
            if(part) { if(part->get_id()==donor) return d; break; }
        }
    }
    return {};
}

inline std::array<double,4> steering(const Controller& ct,const strategy::Memory& memory,Memory& team,int round) {
    std::array<double,4> score{};
    if(ct.get_id()<=1) return score;
    int qid=queen_id(ct); const auto* q=qid<0 ? nullptr : head(ct,qid);
    if(team.approach_until>=0 && round>team.approach_until) {
        team.approach_until=-1; team.retry_after=round+20;
    }
    bool courier=q && !memory.reserve_worker && ct.get_length()>=4 && ct.get_length()<=8
        && ct.get_unit_count()>=4 && round<490 && round>=team.retry_after
        && (team.crowded || round>=200);
    if(courier) for(const auto& t:ct.get_tiles()) {
        const auto* p=t.get_dragon(); if(!p) continue;
        if(p->get_team()!=ct.get_team()) courier=false;
        if(p->is_head() && p->get_id()>1 && p->get_id()<ct.get_id()) courier=false;
    }
    if(courier && team.approach_until<0) team.approach_until=round+6;
    if(!courier) team.approach_until=-1;
    team.mode=courier ? Mode::Approach : (team.crowded ? Mode::Yield : Mode::Harvest);
    for(auto d:Direction::get_direction_list()) {
        Position target; if(!memory.destination(ct,ct.get_position(),d,target)) continue;
        auto& value=score[strategy::Atlas::direction_index(d)];
        if(team.crowded) for(const auto& t:ct.get_tiles()) {
            const auto* p=t.get_dragon();
            if(p && p->is_head() && p->get_team()==ct.get_team() && p->get_id()!=ct.get_id())
                value-=12*std::max(0,3-distance(target,t.get_position()));
        }
        if(courier) { int gap=distance(target,q->get_position()); value+=gap>=2 ? 65.0/(1+std::abs(gap-2)) : -100; }
    }
    return score;
}

inline Plan choose_turn(const Controller& ct,strategy::Memory& memory,Memory& team,int round) {
    Plan plan;
    update_density(team,density(ct));
    auto scores=steering(ct,memory,team,round);
    plan.action=strategy::choose_action(ct,memory,round,!team.crowded && team.mode!=Mode::Approach,scores);
    if(!plan.action.child_size) plan.moves=strategy::plan_moves(ct,memory,plan.action.direction);
    if(ct.get_id()>1) {
        // 声呐不携带可信发送者身份：它只提出候选，绝不能跳过现场验证。
        if(memory.reserve_worker || ct.get_unit_count()<4 || ct.get_length()<4 || ct.get_length()>8 || round>=498) return plan;
        std::optional<Grant> grant;
        for(auto value:ct.get_sonar_messages()) {
            auto g=unpack(value);
            if(!g || g->donor!=ct.get_id() || g->round!=round) continue;
            if(grant) return plan; // 冲突或重复许可一律放弃。
            grant=g;
        }
        if(!grant) return plan;
        const auto* q=head(ct,grant->queen);
        if(!q || q->get_team()!=ct.get_team()) return plan;
        auto qb=complete_body(ct,grant->queen), db=complete_body(ct,ct.get_id());
        if(qb.empty() || db.size()!=static_cast<std::size_t>(ct.get_length())
            || db!=memory.body || !quiet_site(ct,grant->queen,ct.get_id())) return plan;
        auto direction=release_direction(ct); if(!direction) return plan;
        auto drops=drop_cells(db);
        Controller scene=ct; scene.head=*q; scene.length=static_cast<int>(qb.size());
        remove_donor(scene,ct.get_id(),drops);
        auto route=pickup_route(scene,qb,drops,std::max(2,int(drops.size()+1)/2));
        if(route.moves.empty()) return plan;
        team.mode=Mode::Release; plan.action={*direction,0}; plan.moves={*direction};
        plan.telemetry="FEED_RELEASE "+std::to_string(route.food);
        return plan;
    }
    team.mode=Mode::Harvest;
    if(team.receipt_food>0) {
        if(ct.get_length()-team.receipt_length==team.receipt_total)
            plan.telemetry="FEED_RECEIPT "+std::to_string(team.receipt_food);
        team.receipt_food=0;
    }
    if(team.donor>=0) {
        if(round>team.expires || head(ct,team.donor) || !quiet_site(ct,ct.get_id(),team.donor)) {
            team.donor=-1; team.drops.clear(); // 没死亡、过期或现场变化，不追逐承诺中的食物。
        } else {
            if(!team.drop_confirmed) {
                bool pattern=!team.drops.empty();
                for(auto p:team.drops) { const auto* t=ct.get_tile(p); if(!t || !t->has_pearl()) pattern=false; }
                if(!pattern) { team.donor=-1; team.drops.clear(); }
                else team.drop_confirmed=true;
            }
            auto route=pickup_route(ct,memory.body,team.drops,1);
            if(!route.moves.empty()) {
                team.mode=Mode::Collect; plan.action={route.moves.front(),0}; plan.moves=route.moves;
                team.receipt_length=ct.get_length(); team.receipt_total=route.total; team.receipt_food=route.food;
                plan.telemetry+=(plan.telemetry.empty()?"":" ")+std::string("FEED_PICKUP ")+std::to_string(route.food);
                return plan;
            }
            team.donor=-1; team.drops.clear();
        }
    }
    if(round>=498 || round<team.next_grant || ct.get_unit_count()<4 || plan.action.child_size || plan.moves.empty()) return plan;
    Controller projected=ct;
    if(!project(projected,memory,plan.moves)) return plan;
    auto qb=complete_body(projected,ct.get_id());
    if(qb.size()!=static_cast<std::size_t>(projected.get_length())) return plan;
    for(const auto& t:projected.get_tiles()) {
        const auto* p=t.get_dragon();
        if(!p || !p->is_head() || p->get_id()<=1 || p->get_team()!=ct.get_team() || p->get_id()>65535) continue;
        int donor=p->get_id();
        if(!quiet_site(projected,ct.get_id(),donor)) continue;
        auto db=complete_body(projected,donor);
        if(db.size()<4 || db.size()>8) continue;
        auto ray=sonar_to(projected,donor); if(!ray) continue;
        auto drops=drop_cells(db);
        Controller released=projected; remove_donor(released,donor,drops);
        auto route=pickup_route(released,qb,drops,std::max(2,int(drops.size()+1)/2));
        if(route.moves.empty()) continue;
        plan.sonar=std::make_pair(*ray,pack({donor,round,ct.get_id()}));
        team.donor=donor; team.drops=drops; team.expires=round+3; team.next_grant=round+8;
        team.drop_confirmed=false;
        team.mode=Mode::AwaitDrop;
        plan.telemetry+=(plan.telemetry.empty()?"":" ")+std::string("FEED_GRANT ")+std::to_string(donor);
        break; // 每次只能批准一条工兵。
    }
    return plan;
}
} // namespace cooperation
