#include <stdint.h>
using U64=unsigned long long;
__device__ __constant__ U64 IV[8]={0x6a09e667f3bcc908ULL,0xbb67ae8584caa73bULL,0x3c6ef372fe94f82bULL,0xa54ff53a5f1d36f1ULL,0x510e527fade682d1ULL,0x9b05688c2b3e6c1fULL,0x1f83d9abfb41bd6bULL,0x5be0cd19137e2179ULL};
__device__ __constant__ unsigned char SIGMA[12][16]={
 {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},{14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3},
 {11,8,12,0,5,2,15,13,10,14,3,6,7,1,9,4},{7,9,3,1,13,12,11,14,2,6,5,10,4,0,15,8},
 {9,0,5,7,2,4,10,15,14,1,11,12,6,8,3,13},{2,12,6,10,0,11,8,3,4,13,7,5,15,14,1,9},
 {12,5,1,15,14,13,4,10,0,7,6,3,9,2,8,11},{13,11,7,14,12,1,3,9,5,0,15,4,8,6,2,10},
 {6,15,14,9,11,3,0,8,12,2,13,7,1,4,10,5},{10,2,8,4,7,6,1,5,15,11,9,14,3,12,13,0},
 {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},{14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3}};
__device__ U64 rotate(U64 x,int n){return (x>>n)|(x<<(64-n));}
#define G(a,b,c,d,x,y) v[a]+=v[b]+(x);v[d]=rotate(v[d]^v[a],32);v[c]+=v[d];v[b]=rotate(v[b]^v[c],24);v[a]+=v[b]+(y);v[d]=rotate(v[d]^v[a],16);v[c]+=v[d];v[b]=rotate(v[b]^v[c],63)
__device__ void compress(U64* h,const U64* m,unsigned length,bool final){
 U64 v[16];for(int i=0;i<8;i++){v[i]=h[i];v[i+8]=IV[i];}v[12]^=length;if(final)v[14]=~v[14];
 #pragma unroll
 for(int r=0;r<12;r++){
  G(0,4,8,12,m[SIGMA[r][0]],m[SIGMA[r][1]]);G(1,5,9,13,m[SIGMA[r][2]],m[SIGMA[r][3]]);
  G(2,6,10,14,m[SIGMA[r][4]],m[SIGMA[r][5]]);G(3,7,11,15,m[SIGMA[r][6]],m[SIGMA[r][7]]);
  G(0,5,10,15,m[SIGMA[r][8]],m[SIGMA[r][9]]);G(1,6,11,12,m[SIGMA[r][10]],m[SIGMA[r][11]]);
  G(2,7,8,13,m[SIGMA[r][12]],m[SIGMA[r][13]]);G(3,4,9,14,m[SIGMA[r][14]],m[SIGMA[r][15]]);
 }
 for(int i=0;i<8;i++)h[i]^=v[i]^v[i+8];
}
extern "C" __global__ void initialize_midstate(U64* out,unsigned seed,int n,int k){
 U64 h[8],m[16]={0};for(int i=0;i<8;i++)h[i]=IV[i];h[0]^=0x01010000ULL+(512/n)*(n/8);
 h[6]^=0x576f50687361635aULL;h[7]^=(U64)n|((U64)k<<32);m[13]=(U64)seed<<32;compress(h,m,128,false);for(int i=0;i<8;i++)out[i]=h[i];
}
extern "C" __global__ void hash_leaves(const U64* mid,unsigned* out,int count,int n,int k){
 int group=blockIdx.x*blockDim.x+threadIdx.x,per=512/n;if((U64)group*per>=count)return;
 U64 h[8],m[16]={0};for(int i=0;i<8;i++)h[i]=mid[i];m[1]=(U64)(unsigned)group<<32;compress(h,m,144,true);
 int bits=n/(k+1),size=n/8;
 for(int leaf=0;leaf<per;leaf++)if(group*per+leaf<count){
  for(int digit=0;digit<=k;digit++){unsigned value=0;for(int bit=0;bit<bits;bit++){
    int position=leaf*size*8+digit*bits+bit;unsigned char byte=h[position/64]>>(8*((position/8)%8));value=(value<<1)|((byte>>(7-position%8))&1);
  }out[((U64)group*per+leaf)*(k+1)+digit]=value;}
 }
}
extern "C" __global__ void make_keys(const unsigned* hashes,const int* tags,U64* keys,int count,int digits,int bits,int final,int regular){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count)return;
 U64 key=final?((U64)hashes[(U64)i*digits]<<bits)|hashes[(U64)i*digits+1]:hashes[(U64)i*digits];
 if(regular&&!final)key|=(U64)(tags[i]/2)<<bits;keys[i]=key;
}
extern "C" __global__ void pair_counts(const U64* sorted_keys,const unsigned* order,const unsigned* minimum,const int* tags,unsigned* counts,int count,int regular){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count)return;unsigned a=order[i],total=0;
 for(int j=i+1;j<count&&sorted_keys[j]==sorted_keys[i];j++){unsigned b=order[j];if(minimum[a]!=minimum[b]&&(!regular||tags[a]!=tags[b]))total++;}
 counts[i]=total;
}
extern "C" __global__ void emit_pairs(const U64* sorted_keys,const unsigned* order,const unsigned* minimum,const int* tags,const unsigned* hashes,const U64* offsets,const unsigned* vectors,unsigned* new_hashes,unsigned* new_minimum,int* new_tags,unsigned* parents,unsigned* new_vectors,int count,int digits,int width,int final,int regular,int explicit_vectors,int write_parents){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=count)return;unsigned a=order[i];U64 destination=offsets[i];int new_digits=final?1:digits-1;
 for(int j=i+1;j<count&&sorted_keys[j]==sorted_keys[i];j++){
  unsigned b=order[j];if(minimum[a]==minimum[b]||(regular&&tags[a]==tags[b]))continue;
  unsigned left=minimum[a]<minimum[b]?a:b,right=minimum[a]<minimum[b]?b:a;
  if(write_parents){parents[destination*2]=left;parents[destination*2+1]=right;}new_minimum[destination]=minimum[left];new_tags[destination]=regular?tags[a]/2:0;
  for(int d=0;d<new_digits;d++)new_hashes[destination*new_digits+d]=final?0:hashes[(U64)a*digits+d+1]^hashes[(U64)b*digits+d+1];
  if(explicit_vectors)for(int t=0;t<width;t++){new_vectors[destination*width*2+t]=vectors[(U64)left*width+t];new_vectors[destination*width*2+width+t]=vectors[(U64)right*width+t];}
  destination++;
 }
}
