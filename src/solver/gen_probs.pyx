from math import factorial as fac, log, exp
# import time as tm

#xmax, s, m: combs
mult_combs = {
    2: {
        1: {1: 1, 2: 1},
        2: {}
    },
    3: {
    }
}

cdef unsigned long long fac2(int n):
    cdef int i
    cdef unsigned long long ret
    ret = 1
    for i in range(2, n+1):
        ret *= i
    return ret

def combs(int s, int m, int xmax=1):
    if xmax == 1:
        return fac(s) / fac(s - m)
    elif xmax >= m:
        return s**m
    elif m > s*xmax:
        return 0
    elif s == 1:
        return 1
    else:
        try:
            return mult_combs[xmax][s][m]
        except KeyError:
            return find_combs(s, m, xmax)
            # raise ValueError(
            #     "Missing entry for s={}, xmax={}, m={}".format(s, xmax, m))

cdef double cprob(int s, int m, int xmax=1):
    """Calculate the probability a cell contains a mine in a group of size s
    containing m mines and with max per cell of xmax."""
    if m > s*xmax:
        # raise ValueError("Too many mines for group size.")
        return 0
    if xmax == 1:
        return float(m)/s
    elif xmax >= m:
        return 1 - (1 - 1.0/s)**m
    elif m > xmax*(s - 1):
        return 1
    else:
        return 1 - exp( log(combs(s-1, m, xmax)) - log(combs(s, m, xmax)) )

def prob(s, m, xmax=1):
    return cprob(s, m, xmax)

uniquify = lambda x: sorted(list(set(x)))
def set_mult_combs(s, m, xmax, val):
    if not mult_combs[xmax].has_key(s):
        mult_combs[xmax][s] = dict()
    mult_combs[xmax][s][m] = val

def find_combs(int s, int m, int xmax):
    cfgs = [[0]*s]
    end_cfgs = []
    cdef int i, j
    for i in range(s):
        new_cfgs = []
        for c in cfgs:
            for j in range((m - sum(c) - 1)/(s - i) + 1, min(xmax, m - sum(c)) + 1):
                if i != 0 and j > c[i-1]:
                    break
                c1 = c[:]
                c1[i] = j
                if sum(c1) == m:
                    end_cfgs.append(tuple(c1))
                else:
                    new_cfgs.append(c1)
        cfgs = new_cfgs[:]
    cfgs = sorted(end_cfgs, reverse=True)
    cdef int old_max
    cdef float combs, base_combs
    tot = 0
    old_max = 10000
    base_combs = log(fac(s) * fac(m))
    for c in cfgs:
        if max(c) > old_max:
            # Store number for lower xmax.
            set_mult_combs(s, m, old_max, tot)
        old_max = max(c)
        combs = base_combs
        for i in uniquify(c):
            combs -= log(fac(c.count(i)))
            combs -= log(fac(i)**c.count(i))
        tot += exp(combs)
    # set_mult_combs(s, m, xmax, tot)
    return tot



if __name__ == '__main__':
    while True:
        inpt = raw_input("Choose m... ")
        try:
            print find_combs(900, int(inpt), 3)
        except:
            break
