// Original harness around unchanged pinned TCHES artifact functions.
#ifdef PARAM_200
#include "eq200_9/equihash_200_9.h"
#else
#include "eq144_5/equihash_144_5.h"
#endif
extern bool g_verbose;
#include "core/util.h"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sys/resource.h>
std::vector<Solution> run_advanced_cip_pr(int seed,int h,uint8_t* base=nullptr);
int main(int argc,char** argv){
 if(argc!=4)return 1;int seed=std::stoi(argv[1]),height=std::stoi(argv[2]);g_verbose=false;
 auto start=std::chrono::steady_clock::now();auto solutions=run_advanced_cip_pr(seed,height);
 double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
 if(check_zero_xor(seed,solutions)!=solutions.size()){std::cerr<<"Upstream zero-XOR check failed";return 2;}
 struct rusage usage;getrusage(RUSAGE_SELF,&usage);std::ofstream out(argv[3]);if(!out)return 3;
 out<<std::setprecision(17)<<"{\"n\":"<<EquihashParams::N<<",\"k\":"<<EquihashParams::K<<",\"seed\":"<<seed<<",\"height\":"<<height<<",\"solve_wall_ms\":"<<ms<<",\"peak_rss_kib\":"<<usage.ru_maxrss<<",\"solutions\":[";
 for(size_t i=0;i<solutions.size();i++){if(i)out<<",";out<<"[";for(size_t j=0;j<solutions[i].size();j++){if(j)out<<",";out<<solutions[i][j];}out<<"]";}
 out<<"]}\n";
}
