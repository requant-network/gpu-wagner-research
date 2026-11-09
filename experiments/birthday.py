"""Independent canonical Equihash hashing, collision trees and regular GBP."""
import hashlib,itertools,struct

def header(seed):
    result=bytearray(140);struct.pack_into('<I',result,108,seed);return bytes(result)

def leaves(n,k,seed,count=None):
    assert n%8==0 and n%(k+1)==0 and n<=512
    count=count or 1<<(n//(k+1)+1);per_hash=512//n;size=n//8
    person=b'ZcashPoW'+struct.pack('<II',n,k);prefix=header(seed);result=[]
    for group in range((count+per_hash-1)//per_hash):
        digest=hashlib.blake2b(prefix+struct.pack('<I',group),digest_size=per_hash*size,person=person).digest()
        result.extend(int.from_bytes(digest[i*size:(i+1)*size],'big') for i in range(per_hash))
    return result[:count]

def canonical(indices):
    if len(indices)==1:return tuple(indices)
    middle=len(indices)//2;a=canonical(indices[:middle]);b=canonical(indices[middle:])
    return a+b if a[0]<b[0] else b+a

def verify(values,n,k,indices,regular_size=0):
    if len(indices)!=1<<k or len(set(indices))!=len(indices) or any(not 0<=i<len(values) for i in indices):return False
    if regular_size and sorted(i//regular_size for i in indices)!=list(range(1<<k)):return False
    b=n//(k+1)
    def recurse(chain,level):
        if not level:return values[chain[0]]
        mid=len(chain)//2
        if chain[0]>=chain[mid]:raise ValueError('Noncanonical tree order')
        result=recurse(chain[:mid],level-1)^recurse(chain[mid:],level-1)
        remaining=0 if level==k else n-level*b
        if result>>remaining:raise ValueError('Collision prefix does not vanish')
        return result
    try:return recurse(indices,k)==0
    except ValueError:return False

def solve(values,n,k,regular_size=0):
    b=n//(k+1);items=[(value,(i,),i//regular_size if regular_size else 0) for i,value in enumerate(values)];sizes=[len(items)]
    for level in range(k):
        remaining=n-level*b;cut=0 if level==k-1 else remaining-b;groups={}
        for value,chain,tag in items:groups.setdefault((value>>cut,tag//2 if regular_size else 0),[]).append((value,chain,tag))
        result=[]
        for group in groups.values():
            for left,right in itertools.combinations(group,2):
                a,ca,ta=left;c,cc,tc=right
                if regular_size and ta==tc:continue
                if set(ca)&set(cc):continue
                chain=canonical(ca+cc)
                result.append((a^c,chain,ta//2 if regular_size else 0))
        items=result;sizes.append(len(items))
    solutions=sorted(set(chain for value,chain,tag in items if value==0))
    assert all(verify(values,n,k,chain,regular_size) for chain in solutions)
    return solutions,sizes
