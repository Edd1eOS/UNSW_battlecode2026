#pragma once
#include "forage.hpp"

namespace queen120 {
using namespace strategy;
struct Body {
    std::array<int,128> p{};
    int n=0,length=0;
    uint64_t mask=0,eaten=0;
    void remake(){mask=0;for(int i=0;i<n;++i)if(p[i]>=0)mask|=1ULL<<p[i];}
};
struct Board {
    const Controller& ct;const Memory& m;
    std::vector<Position> pos;
    std::vector<int> index;
    std::array<std::array<int,4>,64> edges{};
    std::array<int,64> owner{},team{},facing{};
    uint64_t food=0;
    Board(const Controller& c,const Memory& mem):ct(c),m(mem),index(m.cells.size(),-1){
        owner.fill(-1); team.fill(-1);facing.fill(-1);
        for(auto& t:ct.get_tiles()){index[m.index(t.get_position())]=pos.size();pos.push_back(t.get_position());}
        for(int i=0;i<int(pos.size());++i){
            auto t=ct.get_tile(pos[i]);if(t->has_pearl())food|=1ULL<<i;
            if(auto p=t->get_dragon()){owner[i]=p->get_id();team[i]=p->get_team()==ct.get_team()?0:1;facing[i]=p->is_head()?-1:Atlas::direction_index(p->get_dir());}
            for(int d=0;d<4;++d){Position out; edges[i][d]=-1;
                if(m.destination(ct,pos[i],Direction::get_direction_list()[d],out))edges[i][d]=index[m.index(out)]<0?-2:index[m.index(out)];}
        }
    }
    Body own()const{Body b;b.length=ct.get_length();for(auto p:m.body)if(b.n<128)b.p[b.n++]=index[m.index(p)];b.remake();return b;}
    Body enemy(int head)const{
        Body b;b.p[b.n++]=head;
        while(b.n<64){int prev=-1;for(int i=0;i<int(pos.size());++i)if(owner[i]==owner[head]&&facing[i]>=0&&edges[i][facing[i]]==b.p[b.n-1]&&!(b.mask&(1ULL<<i))){prev=i;break;}
            b.mask|=1ULL<<b.p[b.n-1];if(prev<0)break;b.p[b.n++]=prev;}
        b.length=b.n;return b;
    }
    bool move(Body& b,int to,int id,bool paid,uint64_t blocked=0)const{
        if(to<0 || (paid&&b.length<=2) || (b.mask&(1ULL<<to)) || (blocked&(1ULL<<to)))return false;
        if(owner[to]>=0&&owner[to]!=id&&owner[to]!=ct.get_id())return false;
        if(id==ct.get_id()&&owner[to]>=0&&owner[to]!=id)return false;
        bool grows=(food&(1ULL<<to))&&!(b.eaten&(1ULL<<to));
        if(b.n>=127)return false;
        for(int i=b.n;i>0;--i)b.p[i]=b.p[i-1];b.p[0]=to;++b.n;
        if(grows){++b.length;b.eaten|=1ULL<<to;}
        if(paid)--b.length;
        b.n=std::min(b.n,b.length);b.remake();return true;
    }
    int survive(const Body& b,int depth,int horizon,int& budget)const{
        if(depth>=horizon)return depth;if(--budget<0)return depth;
        int best=depth;
        for(int d=0;d<4;++d){int to=edges[b.p[0]][d];
            if(to==-2){best=std::max(best,horizon-2);continue;}
            Body next=b;if(!move(next,to,ct.get_id(),false))continue;
            best=std::max(best,survive(next,depth+1,horizon,budget));if(best>=horizon)return best;}
        return best;
    }
    bool attack(Body b,int id,int target,uint64_t blocked,int free,int depth,int& budget)const{
        if(depth>=9||--budget<0)return false;
        bool paid=depth>=free;if(paid&&b.length<=2)return false;
        // Manhattan order only orders search; adjacency is always the observed edge graph.
        std::array<int,4> order{0,1,2,3};
        std::sort(order.begin(),order.end(),[&](int a,int z){int x=edges[b.p[0]][a],y=edges[b.p[0]][z];
            return (x<0?999:forage::distance(m,pos[x],pos[target]))<(y<0?999:forage::distance(m,pos[y],pos[target]));});
        for(int d:order){int to=edges[b.p[0]][d];if(to<0||(b.mask&(1ULL<<to))||(blocked&(1ULL<<to)))continue;
            if(to==target)return true;
            Body next=b;if(!move(next,to,id,paid,blocked))continue;
            if(attack(next,id,target,blocked,free,depth+1,budget))return true;}
        return false;
    }
    double danger(const Body& q)const{
        double risk=0;int target=q.p[0];uint64_t block=q.mask&~(1ULL<<target);
        for(int i=0;i<int(pos.size());++i){if(owner[i]<0||owner[i]==ct.get_id()||facing[i]>=0)continue;
            if(team[i]==0){for(int d=0;d<4;++d)if(edges[i][d]==target)risk+=0.15;continue;}
            Body e=enemy(i);e.eaten=q.eaten;int budget=100;
            if(attack(e,owner[i],target,block,(e.length+3)/4,0,budget))risk+=1;
            // A partial tail is not evidence that the attacker is short.
            bool partial=false;for(int d=0;d<4;++d)if(edges[e.p[e.n-1]][d]==-2)partial=true;
            if(partial){Body big=e;big.length=std::max(6,e.length);budget=60;if(attack(big,owner[i],target,block,(big.length+3)/4,0,budget))risk+=0.65;}
            // Newborns act on the split round; the old rear becomes their head.
            for(int size=2;size<=std::min(4,e.n-2);++size){Body child;child.length=child.n=size;child.eaten=q.eaten;
                for(int j=0;j<size;++j)child.p[j]=e.p[e.n-1-j];child.remake();budget=35;
                uint64_t parent=0;for(int j=0;j<e.n-size;++j)parent|=1ULL<<e.p[j];
                if(attack(child,owner[i],target,block|parent,(size+3)/4,0,budget)){risk+=0.9;break;}}
        }
        return risk;
    }
};
inline forage::Plan choose(const Controller& ct,Memory& m,forage::State& state){
    if(m.body.empty()||m.body.size()!=size_t(ct.get_length())||ct.get_length()>110||ct.get_tiles().size()>63)return forage::choose(ct,m,state);
    Board b(ct,m);Body initial=b.own();if(initial.p[0]<0)return forage::choose(ct,m,state);
    const int goal=forage::select_goal(ct,m,state);
    auto field=goal>=0?forage::distances(ct,m,forage::position(m,goal),true):std::vector<int>(m.cells.size(),0);
    int free=(ct.get_length()+3)/4,limit=std::min(8,free+2),nodes=0;
    double best=-1e30;std::vector<Direction> path;
    forage::Plan plan{{ct.get_dir(),0},{},"V120 QUEEN"};
    auto score=[&](const Body& q,int child){
        int budget=130,horizon=std::min(16,std::max(10,q.length+2));int depth=b.survive(q,0,horizon,budget);
        double risk=b.danger(q);auto end=b.pos[q.p[0]];
        double value=190*(q.length-initial.length)-12*std::min(field[m.index(end)],80);
        value-=risk*4500;value-=depth>=horizon-2?0:2400+160*(horizon-depth);
        value+=2*depth;value-=2*m.visits(end)+0.3*std::min(30,m.lifetime_visits(end));
        value-=0.5*path.size();if(child)value-=40;
        if(value>best){best=value;plan.action.child_size=child;plan.moves=path;if(!path.empty())plan.action.direction=path.front();}
    };
    auto visit=[&](auto&& self,const Body& cur)->void{
        if(int(path.size())>=limit||nodes>=160)return;
        for(int d=0;d<4;++d){Body next=cur;if(!b.move(next,b.edges[cur.p[0]][d],ct.get_id(),int(path.size())>=free))continue;
            ++nodes;path.push_back(Direction::get_direction_list()[d]);score(next,0);self(self,next);path.pop_back();if(nodes>=160)break;}
    };visit(visit,initial);
    // Splits compete with movement using the same post-action threat calculation.
    if(ct.can_split(2)){Body q=initial;q.length-=2;q.n-=2;q.remake();score(q,2);}
    if(plan.moves.empty()&&!plan.action.child_size)return forage::choose(ct,m,state);
    plan.note+=" score="+std::to_string(int(best))+" nodes="+std::to_string(nodes);
    return plan;
}
}
