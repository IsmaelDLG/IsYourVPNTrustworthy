from datasketch import MinHash, MinHashLSH

# http://ekzhu.com/datasketch/lsh.html

NUM_PERM = 128
THRESHOLD = 0.5

set1 = set(['minhash', 'is', 'a', 'probabilistic', 'data', 'structure', 'for',
            'estimating', 'the', 'similarity', 'between', 'datasets'])
set2 = set(['minhashaa', 'isdf', 'a', 'probabilccity', 'data', 'structure', 'for',
            'estimating', 'the', 'similarity', 'between', 'documents'])
set3 = set(['minhash', 'is', 'probability', 'data', 'structure', 'for',
            'estimating', 'the', 'similarity', 'between', 'documents'])

m1 = MinHash(num_perm=NUM_PERM)
m2 = MinHash(num_perm=NUM_PERM)
m3 = MinHash(num_perm=NUM_PERM)
for d in set1:
    m1.update(d.encode('utf8'))
for d in set2:
    m2.update(d.encode('utf8'))
for d in set3:
    m3.update(d.encode('utf8'))

# Create LSH index
lsh = MinHashLSH(threshold=THRESHOLD, num_perm=NUM_PERM)
lsh.insert("m2", m2)
lsh.insert("m3", m3)
result = lsh.query(m1)
print("Approximate neighbours with Jaccard similarity > 0.5", result)