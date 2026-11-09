// Original API wrapper; the canonical hashing/verifier comes from equi.h.
#include "equi.h"
static void make_header(unsigned seed,char* result){memset(result,0,140);result[108]=seed;result[109]=seed>>8;result[110]=seed>>16;result[111]=seed>>24;}
extern "C" int requant_verify(unsigned seed,unsigned* indices){char header[140];make_header(seed,header);return verify(indices,header,140,"ZcashPoW");}
extern "C" void requant_leaf(unsigned seed,unsigned index,unsigned char* out){char header[140];make_header(seed,header);blake2b_state state;setheader(&state,header,"ZcashPoW");genhash(&state,index,out);}
