#!/usr/bin/env python
import sys
import shutil
import os

"""
This tool extract blocks from a possible corrupted file in the order given 
by the block_order_file. The layout of the block_order_file is the following:
offset-size
657457152-3145728
150994944-3145728
355467264-3145728
"""

# TODO: improve with flags

chunk_folder="./chunks"
try:
    shutil.rmtree(chunk_folder)
except:
    pass
    
os.mkdir(chunk_folder)


if len(sys.argv) < 3:
    print "Usage: %s <corrupted-file> <block-order-file>" % (sys.argv[0])
    sys.exit(1)

corrupted_file=sys.argv[1]
block_order_file=sys.argv[2]

lines = [line.rstrip('\n') for line in open(block_order_file)]
chunks=[]
for line in lines:
    tokens=line.split("-")
    offset,size=int(tokens[0]),int(tokens[1])
    chunks.append((offset,size))

#chunks=[(0,3),(9,0.1),(3,3),(6,3)]
n=len(chunks)
corrupted_index=zip(range(n),chunks)
source_index=zip(range(n),sorted(chunks))          
source_index_map = dict([(x[1],x[0]) for x in source_index])
c=0
for i,r in corrupted_index:
    chunk_fn=os.path.join(chunk_folder, str(source_index_map[r]+1))
    print "read corrupted file from offset=%d size_bytes=%d -> save as chunk index=%03d" % (c,r[1],source_index_map[r]+1) 
    cmd="dd if=%s of=%s bs=%d count=1 skip=%d iflag=skip_bytes" % (corrupted_file,chunk_fn,r[1],c) 
    print cmd
    os.system(cmd)
    c += r[1]
