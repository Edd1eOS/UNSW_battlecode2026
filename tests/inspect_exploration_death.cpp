#include "../opponents/generalist-exploration-v1/planner.hpp"
#include <iostream>

// Read-only continuous protocol inspector. It never supplies hidden state.
bool first_route(const unswbc::Controller& ct,const strategy::Memory& m,
                 const strategy::Simulation& s,int depth,int horizon,int& budget,
                 std::vector<unswbc::Position>& route) {
 if(depth>=horizon)return true;
 if(budget--<=0)return false;
 for(auto d:unswbc::Direction::get_direction_list()) {
  unswbc::Position to;
  if(!m.destination(ct,s.body.front(),d,to)||!ct.get_tile(to))continue;
  auto next=s;if(!planner::step(ct,m,next,d,false))continue;
  route.push_back(to);
  if(first_route(ct,m,next,depth+1,horizon,budget,route))return true;
  route.pop_back();
 }
 return false;
}
int main() {
 auto [ct,game]=unswbc::init();strategy::Memory memory;planner::State state;
 while(unswbc::update(ct,game)) {
  planner::observe(ct,memory,state);memory.remember(ct.get_position());
  const auto before=planner::initial(ct,memory);
  std::vector<double> enemy_danger;
  const auto danger=planner::risks(ct,memory,nullptr,&enemy_danger);
  auto plan=planner::choose(ct,memory,state);
  std::cout<<"TRACE "<<game.get_round_num()<<" id="<<ct.get_id()<<" head="<<ct.get_position().x<<","<<ct.get_position().y
   <<" length="<<ct.get_length()<<" complete="<<before.complete<<" body=";
  for(auto p:before.body)std::cout<<p.x<<","<<p.y<<";";
  std::cout<<" selected=";for(auto d:plan.moves)std::cout<<d.value;
  std::cout<<" child="<<plan.action.child_size;
  std::cout<<" "<<plan.note;
  for(auto d:unswbc::Direction::get_direction_list()) {
   unswbc::Position to;std::cout<<" ALT:"<<d.value;
   if(!memory.destination(ct,ct.get_position(),d,to)){std::cout<<" unresolved_or_wall";continue;}
   std::cout<<"->"<<to.x<<","<<to.y;
   if(!ct.get_tile(to)){std::cout<<" outside_current_view";continue;}
   auto s=before;
   if(!planner::step(ct,memory,s,d,false)) {
    const auto* p=ct.get_tile(to)->get_dragon();
    std::cout<<" blocked";if(p)std::cout<<"_id"<<p->get_id();continue;
   }
   int budget=ct.get_id()<=1?140:90;const int horizon=ct.get_id()<=1?8:6;
   auto f=planner::continuation(ct,memory,s,{},0,horizon,budget);
   std::cout<<" grade"<<planner::future_grade(f,horizon)<<" depth"<<f.depth<<" outside"<<f.outside<<" portal"<<f.portal<<" risk"<<danger[memory.index(to)];
   if(f.depth>=horizon){std::vector<unswbc::Position> route;int route_budget=300;
    if(first_route(ct,memory,s,0,horizon,route_budget,route)){std::cout<<" route=";for(auto p:route)std::cout<<p.x<<","<<p.y<<";";}
   }
  }
  // Enumerate legal two-step paid alternatives at length three. These are
  // local certificates only, not a replay of a counterfactual later match.
  if(ct.get_id()<=1&&ct.get_length()==3&&plan.moves.size()==1&&!plan.uncertain) {
   planner::Candidate free;free.simulation=before;free.moves=plan.moves;
   if(planner::step(ct,memory,free.simulation,plan.moves.front(),false)) {
    int fb=140;free.future=planner::continuation(ct,memory,free.simulation,{},0,8,fb);
    free.enemy_risk=enemy_danger[memory.index(free.simulation.body.front())];
    for(auto a:unswbc::Direction::get_direction_list())for(auto b:unswbc::Direction::get_direction_list()) {
     if(a==ct.get_dir().get_opposite())continue;
     planner::Candidate paid;paid.simulation=before;paid.moves={a,b};paid.paid=1;
     if(!planner::step(ct,memory,paid.simulation,a,false)||!planner::step(ct,memory,paid.simulation,b,true))continue;
     paid.food=static_cast<int>(paid.simulation.eaten.size());int pb=140;
     paid.future=planner::continuation(ct,memory,paid.simulation,{},0,8,pb);
     paid.enemy_risk=enemy_danger[memory.index(paid.simulation.body.front())];
     std::cout<<" PAID:"<<a.value<<b.value<<"->"<<paid.simulation.body.front().x<<","<<paid.simulation.body.front().y
      <<" length"<<paid.simulation.length<<" grade"<<planner::future_grade(paid.future,8)
      <<" capital_dominated"<<planner::capital_dominated(paid,free,8);
    }
   }
  }
  std::cout<<"\n";
  planner::remember(ct,memory,state,plan,game.get_round_num());
 }
}
