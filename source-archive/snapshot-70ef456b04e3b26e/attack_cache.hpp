#pragma once
// Included inside namespace human, after Map. Only the Queen uses this cache.
struct AttackCache {
    struct Enemy {int id=0,minimum=2,potential=5;bool complete=false;std::vector<int> body;std::vector<int> body_index;};
    struct Route {int enemy=0,count=0;std::array<int,4> cells{};};
    struct Threat {int certain=0,potential=0;};
    const Controller& ct;const Memory& m;
    std::vector<Enemy> enemies;
    std::vector<std::vector<Route>> endings;
    int path_count=0;bool truncated=false;
    AttackCache(const Controller& control,const Memory& memory,const Map& graph):ct(control),m(memory),endings(memory.cells.size()) {
        if(ct.get_id()>1)return;
        for(const auto& tile:ct.get_tiles()) {
            const auto* head=tile.get_dragon();if(!head||!head->is_head()||head->get_team()==ct.get_team())continue;
            Enemy e;e.id=head->get_id();e.body.push_back(m.index(tile.get_position()));
            int observed=0;for(const auto& segment:ct.get_tiles())if(segment.get_dragon()&&segment.get_dragon()->get_id()==e.id)++observed;
            while((int)e.body.size()<observed) {
                bool added=false;for(const auto& segment:ct.get_tiles()) {const auto* part=segment.get_dragon();Position toward;
                    if(!part||part->get_id()!=e.id||part->is_head())continue;int at=m.index(segment.get_position());
                    if(std::find(e.body.begin(),e.body.end(),at)!=e.body.end())continue;
                    if(m.destination(ct,segment.get_position(),part->get_dir(),toward)&&m.index(toward)==e.body.back()) {e.body.push_back(at);added=true;break;}
                }if(!added)break;
            }
            e.complete=(int)e.body.size()==observed&&observed>=2;
            const auto* tail=ct.get_tile(pos(m,e.body.back()));
            if(e.complete&&tail)for(auto direction:Direction::get_direction_list()) {
                if(tail->get_edge(direction).get_edge_type()==EdgeType::KELP)continue;Position next;
                if(!m.destination(ct,tail->get_position(),direction,next)||!ct.get_tile(next))e.complete=false;
            }
            e.minimum=std::max(2,observed);e.potential=e.complete?e.minimum:std::max(5,e.minimum);
            e.body_index.assign(m.cells.size(),-1);for(int i=0;i<(int)e.body.size();++i)e.body_index[e.body[i]]=i;
            int enemy=(int)enemies.size();enemies.push_back(std::move(e));Route path;path.enemy=enemy;
            auto visit=[&](auto&& self,int at)->void {
                if(path.count>=4)return;
                for(int next:graph.next[at]) {
                    if(next<0||!ct.get_tile(pos(m,next))||next==enemies[enemy].body.front())continue;
                    if(std::find(path.cells.begin(),path.cells.begin()+path.count,next)!=path.cells.begin()+path.count)continue;
                    const auto* part=ct.get_tile(pos(m,next))->get_dragon();
                    if(part&&part->get_id()!=ct.get_id()&&part->get_id()!=enemies[enemy].id)continue;
                    if(path_count>=4096){truncated=true;return;}
                    path.cells[path.count++]=next;endings[next].push_back(path);++path_count;
                    self(self,next);--path.count;
                }
            };visit(visit,enemies[enemy].body.front());
        }
    }
    bool executable(const Route& route,const Simulation& queen,int initial_length) const {
        const auto& enemy=enemies[route.enemy];int length=initial_length,free=(initial_length+3)/4;
        const int target=m.index(queen.body.front());
        for(int step=0;step<route.count;++step) {
            bool paid=step>=free;if(paid&&length<=2)return false;
            int at=route.cells[step];Position point=pos(m,at);const auto* tile=ct.get_tile(point);
            if(!tile)return false;const auto* part=tile->get_dragon();
            if(part&&part->get_id()!=ct.get_id()&&part->get_id()!=enemy.id)return false;
            // Collision occurs before food and before either tail removal.
            if(at!=target&&std::find(queen.body.begin(),queen.body.end(),point)!=queen.body.end())return false;
            if(enemy.complete) {
                int old_kept=std::max(0,std::min((int)enemy.body.size(),length-step));
                if(enemy.body_index[at]>=0&&enemy.body_index[at]<old_kept)return false;
            } else if(part&&part->get_id()==enemy.id)return false;
            // Routes are simple, but retain the exact new-body check explicitly.
            for(int previous=std::max(0,step-length);previous<step;++previous)if(route.cells[previous]==at)return false;
            if(at==target)return true; // The head collision ends the attack.
            bool pearl=tile->has_pearl()&&std::find(queen.eaten.begin(),queen.eaten.end(),point)==queen.eaten.end();
            for(int previous=0;previous<step;++previous)if(route.cells[previous]==at)pearl=false;
            if(pearl)++length;if(paid)--length;
        }return false;
    }
    Threat assess(const Simulation& queen) const {
        Threat result;if(queen.body.empty())return result;std::vector<unsigned char> seen(enemies.size(),0);
        for(const auto& route:endings[m.index(queen.body.front())]) {
            if(seen[route.enemy]==2)continue;const auto& enemy=enemies[route.enemy];
            if(executable(route,queen,enemy.minimum))seen[route.enemy]=2;
            else if(!enemy.complete&&seen[route.enemy]==0&&executable(route,queen,enemy.potential))seen[route.enemy]=1;
        }
        for(auto state:seen){if(state==2)++result.certain;else if(state==1)++result.potential;}return result;
    }
};
