using uint32_t = unsigned int;
using uint8_t = unsigned char;
extern "C" __global__ void pack24(const uint32_t* source,uint8_t* target,int count){
    int i=blockIdx.x*256+threadIdx.x;if(i>=count)return;
    uint32_t x=source[i];target[(size_t)i*3]=x;target[(size_t)i*3+1]=x>>8;target[(size_t)i*3+2]=x>>16;
}
extern "C" __global__ void gather24(const uint8_t* source,const uint32_t* indices,uint32_t* target,int count){
    int i=blockIdx.x*256+threadIdx.x;if(i>=count*2)return;
    size_t offset=((size_t)indices[i/2]*2+i%2)*3;
    target[i]=uint32_t(source[offset])|(uint32_t(source[offset+1])<<8)|(uint32_t(source[offset+2])<<16);
}
