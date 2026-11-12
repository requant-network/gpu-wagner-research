// The pinned Tromp solver on exactly the canonical header used by the GPU study.
#include "equi_miner.h"
#include <chrono>
#include <iostream>
#include <iomanip>
#include <sys/resource.h>
#include <vector>
int main(int argc,char** argv){
    if(argc!=3)return 1;
    unsigned seed=std::stoul(argv[1]);int count=std::stoi(argv[2]);
    if(count<1||count>6)return 1;
    #ifndef ATOMIC
    if(count!=1)return 1;
    #endif
    auto start=std::chrono::steady_clock::now();
    equi solver(count);char header[140]={0};
    for(int i=0;i<4;i++)header[108+i]=seed>>(8*i);
    solver.setheadernonce(header,140,"ZcashPoW");
    std::vector<thread_ctx> threads(count);
    for(int i=0;i<count;i++){
        threads[i].id=i;threads[i].eq=&solver;
        if(pthread_create(&threads[i].thread,nullptr,worker,&threads[i]))return 2;
    }
    for(auto& thread:threads)if(pthread_join(thread.thread,nullptr))return 2;
    double elapsed=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    unsigned raw=solver.nsols,retained=std::min(raw,MAXSOLS);rusage usage{};getrusage(RUSAGE_SELF,&usage);
    std::cout<<"\nRESULT {\"n\":"<<WN<<",\"k\":"<<WK<<",\"seed\":"<<seed<<",\"threads\":"<<count
             <<",\"solve_reconstruction_ms\":"<<std::setprecision(17)<<elapsed<<",\"peak_rss_kib\":"<<usage.ru_maxrss
             <<",\"raw_solution_count\":"<<raw<<",\"solution_capacity\":"<<MAXSOLS<<",\"solutions\":[";
    for(unsigned i=0;i<retained;i++){
        if(i)std::cout<<",";std::cout<<"[";
        for(unsigned j=0;j<PROOFSIZE;j++){if(j)std::cout<<",";std::cout<<solver.sols[i][j];}
        std::cout<<"]";
    }
    std::cout<<"]}\n";
}
