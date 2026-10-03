#include "../opponents/v76-collector-delivery/cooperation.hpp"
#include <cassert>
#include <iostream>
using namespace unswbc;
struct FeedingScene {
    Game board{15,15,64};
    Controller bot{0,Team::A,Direction::EAST,Vision{},64};
    strategy::Memory memory;
    cooperation::Memory team;
    std::deque<Position> queen{{5,5},{4,5},{4,4},{4,3},{5,3},{6,3},{7,3},{7,4},{7,5}};
    std::deque<Position> donor{{6,4},{6,5},{6,6},{7,6}};
    FeedingScene() {
        game=&board; ct=&bot; board.round_num=220;
        std::vector<Tile> tiles;
        for(int y=2;y<=8;++y) for(int x=2;x<=8;++x) tiles.emplace_back(Position{x,y});
        bot.vision=Vision{std::move(tiles)};
        add(queen,0,Team::A); add(donor,2,Team::A);
        bot.head=*bot.get_tile(queen.front())->get_dragon(); bot.length=9; bot.unit_count=4;
        memory.observe(bot); memory.remember(bot.get_position());
    }
    void add(const std::deque<Position>& body,int id,Team team) {
        for(std::size_t i=0;i<body.size();++i) {
            Direction direction=Direction::NORTH;
            auto dest=i ? body[i-1] : body[0];
            auto from=i ? body[i] : body[1];
            for(auto d:Direction::get_direction_list()) if(from.add_dir(d)==dest) direction=d;
            bot.get_tile(body[i])->dragon_part=DragonPart{body[i],id,team,direction,i==0};
        }
    }
};

int main() {
    { cooperation::Memory m;
      cooperation::update_density(m,{49,18,2}); assert(m.crowded);
      cooperation::update_density(m,{49,10,2}); assert(m.crowded);
      cooperation::update_density(m,{49,14,2}); assert(m.crowded && m.clear_turns==0);
      for(int i=0;i<3;++i) cooperation::update_density(m,{49,10,2});
      assert(!m.crowded);
      cooperation::update_density(m,{49,5,4}); assert(m.crowded); }
    { FeedingScene s;
      assert(cooperation::complete_body(s.bot,2)==s.donor);
      s.bot.vision.tiles_by_position.erase({8,6}); // 尾部邻域缺失，不能声称看全身体。
      assert(cooperation::complete_body(s.bot,2).empty()); }
    { FeedingScene s;
      auto q=cooperation::complete_body(s.bot,0); assert(q==s.queen);
      Controller scene=s.bot;
      assert(cooperation::project(scene,s.memory,{Direction::SOUTH}));
      auto qb=cooperation::complete_body(scene,0); assert(qb.size()==9);
      auto drops=cooperation::drop_cells(s.donor); assert(drops.size()==2);
      assert(drops[0]==Position(6,4) && drops[1]==Position(6,6));
      assert(cooperation::sonar_to(scene,2)==Direction(Direction::EAST));
      cooperation::remove_donor(scene,2,drops);
      auto route=cooperation::pickup_route(scene,qb,drops,2);
      assert(route.food==2 && route.moves.size()==3);
      assert(route.moves[0]==Direction(Direction::EAST)); }
    { FeedingScene s; Controller scene=s.bot;
      assert(cooperation::project(scene,s.memory,{Direction::SOUTH}));
      auto qb=cooperation::complete_body(scene,0);
      for(Position p: {Position{5,7},Position{6,7},Position{7,7}}) scene.get_tile(p)->pearl=true;
      assert(cooperation::delivery_route(scene,qb,s.donor,2).moves.empty()); }
    { FeedingScene s; Controller scene=s.bot;
      assert(cooperation::project(scene,s.memory,{Direction::SOUTH}));
      auto qb=cooperation::complete_body(scene,0);
      auto wall=[&](Position p,Direction d) {
          scene.get_tile(p)->get_edge(d).edge_type=EdgeType::KELP;
          scene.get_tile(p.add_dir(d))->get_edge(d.get_opposite()).edge_type=EdgeType::KELP;
      };
      wall({6,6},Direction::EAST); wall({6,6},Direction::SOUTH);
      wall({6,5},Direction::EAST); wall({6,5},Direction::WEST);
      wall({6,4},Direction::EAST); wall({6,4},Direction::WEST);
      assert(cooperation::delivery_route(scene,qb,s.donor,2).moves.empty()); // 食物尽头没有退路。
    }
    { FeedingScene s;
      auto plan=cooperation::choose_turn(s.bot,s.memory,s.team,220);
      assert(plan.sonar && s.team.mode==cooperation::Mode::AwaitDrop);
      auto grant=cooperation::unpack(plan.sonar->second); assert(grant && grant->donor==2 && grant->round==(220&63));
      Controller actual=s.bot; assert(cooperation::project(actual,s.memory,plan.moves));
      // donor 看 Queen 行动后的局面。放大为实际 donor 的 7x7 视野。
      std::vector<Tile> tiles;
      for(int y=1;y<=7;++y) for(int x=3;x<=9;++x) {
          const auto* t=actual.get_tile({x,y}); tiles.push_back(t ? *t : Tile{{x,y}});
      }
      actual.vision=Vision{std::move(tiles)};
      actual.head=*actual.get_tile(s.donor.front())->get_dragon(); actual.length=4;
      actual.sonar_messages={plan.sonar->second};
      strategy::Memory worker; worker.observe(actual); worker.remember(actual.get_position());
      cooperation::Memory worker_team;
      auto release=cooperation::choose_turn(actual,worker,worker_team,220);
      assert(worker_team.mode==cooperation::Mode::Release);
      assert(release.telemetry=="FEED_RELEASE 2");
      auto next=actual.get_tile(actual.get_position().add_dir(release.moves.front()));
      assert(next && next->get_dragon() && next->get_dragon()->get_id()==2); // 只能自撞，不能撞 Queen。
      cooperation::Memory stale;
      assert(cooperation::choose_turn(actual,worker,stale,221).telemetry.empty());
      actual.sonar_messages.push_back(plan.sonar->second);
      cooperation::Memory conflict; assert(cooperation::choose_turn(actual,worker,conflict,220).telemetry.empty());
      actual.sonar_messages.resize(1);
      actual.get_tile({8,4})->dragon_part=DragonPart{{8,4},3,Team::B,Direction::WEST,true};
      cooperation::Memory enemy; assert(cooperation::choose_turn(actual,worker,enemy,220).telemetry.empty());
      actual.get_tile({8,4})->dragon_part=DragonPart{{8,4},4,Team::A,Direction::WEST,true};
      cooperation::Memory ally; assert(cooperation::choose_turn(actual,worker,ally,220).telemetry.empty());
      actual.get_tile({8,4})->dragon_part.reset(); worker.reserve_worker=true;
      cooperation::Memory reserve; assert(cooperation::choose_turn(actual,worker,reserve,220).telemetry.empty());
      worker.reserve_worker=false; actual.unit_count=2;
      cooperation::Memory few; assert(cooperation::choose_turn(actual,worker,few,220).telemetry.empty());
      // Queen 下一回合必须看到实际掉落，不能根据承诺穿过活工兵。
      Controller queen=s.bot; assert(cooperation::project(queen,s.memory,plan.moves));
      strategy::Memory qm; qm.body=cooperation::complete_body(queen,0); qm.observe(queen);
      auto pending=s.team;
      auto denied=cooperation::choose_turn(queen,qm,pending,221);
      assert(pending.donor==-1 && pending.mode!=cooperation::Mode::Collect);
      cooperation::remove_donor(queen,2,s.team.drops);
      auto collect=cooperation::choose_turn(queen,qm,s.team,221);
      assert(s.team.mode==cooperation::Mode::Collect && collect.moves.size()==3);
      assert(cooperation::project(queen,qm,collect.moves));
      qm.body=cooperation::complete_body(queen,0); qm.observe(queen);
      auto receipt=cooperation::choose_turn(queen,qm,s.team,222);
      assert(queen.length==11 && receipt.telemetry.find("FEED_RECEIPT 2")!=std::string::npos); }
    { FeedingScene s;
      auto p=cooperation::choose_turn(s.bot,s.memory,s.team,498); assert(!p.sonar);
      assert(cooperation::quiet_site(s.bot,0,2));
      s.bot.get_tile({8,8})->dragon_part=DragonPart{{8,8},5,Team::B,Direction::NORTH,false};
      assert(!cooperation::quiet_site(s.bot,0,2)); }
    { FeedingScene s;
      auto base=strategy::choose_action(s.bot,s.memory,220);
      auto disabled=cooperation::choose_turn(s.bot,s.memory,s.team,220,{false,false,false});
      assert(base.direction==disabled.action.direction && base.child_size==disabled.action.child_size);
      assert(!disabled.sonar && disabled.telemetry.empty()); }
    { auto v=cooperation::pack({2047,497,17}); assert(v<=UINT32_MAX);
      auto g=cooperation::unpack(v); assert(g && g->round==(497&63) && g->donor==2047 && g->queen==17);
      assert(!cooperation::unpack(1234)); }
    { FeedingScene s;
      cooperation::Plan base; base.action={Direction::SOUTH,0};base.moves={Direction::SOUTH};
      auto p=cooperation::choose_turn(s.bot,s.memory,s.team,220,{false,false,false},&base);
      assert(p.moves==base.moves && p.action.direction==base.action.direction);
      // Two-segment donor can deliver one pearl; no speculative disappearance.
      for(auto pos:s.donor) s.bot.get_tile(pos)->dragon_part.reset();
      s.donor={{6,6},{7,6}};s.add(s.donor,2,Team::A);
      Controller projected=s.bot;assert(cooperation::project(projected,s.memory,base.moves));
      auto qb=cooperation::complete_body(projected,0);
      auto route=cooperation::delivery_route(projected,qb,s.donor,2);
      assert(route.food==1 && !route.moves.empty());
      auto grant=cooperation::choose_turn(s.bot,s.memory,s.team,220,{false,false,true},&base);
      assert(grant.sonar && grant.moves==base.moves);
    }
    { FeedingScene s;
      for(auto& tile:s.bot.vision.tiles) if(tile.dragon_part) tile.dragon_part->dragon_id=tile.dragon_part->dragon_id==0?4:8;
      s.bot.head.dragon_id=4;cooperation::Plan base;base.action={Direction::SOUTH,0};base.moves={Direction::SOUTH};
      auto p=cooperation::choose_turn(s.bot,s.memory,s.team,220,{false,false,true},&base,true);
      assert(p.sonar);auto grant=cooperation::unpack(p.sonar->second);
      assert(grant && grant->queen==4 && grant->donor==8);
    }
    std::cout<<"Cooperation: congestion, complete bodies, grants, release, cancellation, collection and receipt passed\n";
}
