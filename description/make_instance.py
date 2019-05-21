import itertools
import random

n = 12 
m = 15
edge_size = 3

comb = [c for c in itertools.combinations(range(n), edge_size)]
random.shuffle(comb)
comb = comb[:m]
comb.sort()

print "p htd {} {}".format(n, m)
for i, c in enumerate(comb):
    print i+1, " ".join(str(x+1) for x in c)
