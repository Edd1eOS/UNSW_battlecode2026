#include "../opponents/generalist-v5/planner.hpp"
#include <iostream>
int main(){
 auto [ct,game]=unswbc::init();strategy::Memory memory;planner::State state;
 while(unswbc::update(ct,game)){
  planner::observe(ct,memory,state);memory.remember(ct.get_position());
  auto plan=planner::choose(ct,memory,state);
  planner::State inspect=state;auto graph=planner::goals(ct,memory,inspect);
  int known=0;for(const auto& cell:memory.cells)known+=cell.known;
  std::cout<<"TRACE "<<game.get_round_num()<<" "<<ct.get_position().x<<","<<ct.get_position().y
   <<" known="<<known<<" targets="<<graph.food_sites<<" frontier="<<graph.frontiers<<" selected=";
  for(auto d:plan.moves)std::cout<<d.value;
  std::cout<<" "<<plan.note;
  for(auto d:unswbc::Direction::get_direction_list()){
   if(ct.get_length()>=2&&d==ct.get_dir().get_opposite())continue;
   unswbc::Position to;const auto* here=ct.get_tile(ct.get_position());
   if(!memory.destination(ct,ct.get_position(),d,to)){
    if(here->get_edge(d).is_portal())std::cout<<" ALT:"<<d.value<<" unresolved_portal grade2";
    continue;
   }
   auto sim=planner::initial(ct,memory);
   if(!ct.get_tile(to)){std::cout<<" ALT:"<<d.value<<" outside grade2";continue;}
   if(!planner::step(ct,memory,sim,d,false))continue;
   int budget=ct.get_id()<=1?140:90;int horizon=ct.get_id()<=1?8:6;
   auto future=planner::continuation(ct,memory,sim,{},0,horizon,budget);
   std::cout<<" ALT:"<<d.value<<" grade"<<planner::future_grade(future,horizon)
    <<" depth"<<future.depth<<" outside"<<future.outside<<" portal"<<future.portal;
  }
  std::cout<<"\n";
  planner::remember(ct,memory,state,plan,game.get_round_num());
 }
}
