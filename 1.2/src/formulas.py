from math import factorial as fac

import matplotlib.pyplot as plt


def p(s, a, xmax=2):
    """
    Calculate the probability of all cells obeying the limit in a group of
    size s with a mines placed randomly.
    """
    if s == 2:
        ret = 0
        for x2 in range(0, xmax + 1):
            ret += fac(a)/(fac(x2) * fac(a-x2))
        ret *= 2**(-a)
        return ret
    if s != 3:
        raise ValueError("Only works for s=3 currently.")
    ret = 0
    for x1 in range(max(0, a - 2*xmax), xmax+1):
        for x2 in range(max(0, a - xmax - x1), min(xmax, a - x1) + 1):
            ret += fac(a)/(fac(x1) * fac(x2) * fac(a-x1-x2))
    ret *= 3**(-a)
    return ret


def p2(s, a, xmax=2):
    """
    Calculate the probability of all cells obeying the limit in a group of
    size s with a mines placed randomly.
    """
    def nextsum(dummies):
        subprob = 0
        for i in range(0, min(xmax, a - sum(dummies)) + 1):
            subprob += (binom(i, a - sum(dummies), 1/(s-len(dummies)))
                        * nextsum(dummies + [i]))
        return subprob
                        
    ret = 0

    
    # Initialise dummy variables.
    dummies = (s-1)*[0]
        
    for x1 in range(max(0, a - 2*xmax), xmax+1):
        for x2 in range(max(0, a - xmax - x1), min(xmax, a - x1) + 1):
            ret += fac(a)/(fac(x1) * fac(x2) * fac(a-x1-x2))
    ret *= 3**(-a)
    return ret




def binom(x1, n, p, x2=None):
    nfac = fac(n)
    if not x2:
        x2 = x1
    prob = 0
    for i in xrange(x1, x2 + 1):
        prob += float(1)/(fac(i) * fac(n - i)) * (p / (1 - p))**i
    prob *= fac(n) * (1 - p)**n
    return prob


def prob(s, a, xmax=1e6):
    """
    Calculate the probability a cell contains a mine in a group of size s
    containing a mines and with max per cell of xmax.
    """
    if a > s*xmax:
        raise ValueError("Too many mines for group size.")
    if xmax == 1:
        return float(a)/s
    p0 = (float(s - 1) / s)**a
    if xmax > a:
        return 1 - p0
    else:
        return 1 - p(s-1,a,xmax)/p(s,a,xmax) * p0


def run(s):
    for xmax in [1, 2, 3, 4, 1e5]:
        a_list = range(s * min(xmax,5) + 1)
        plt.plot(a_list, map(lambda a: prob(s, a, xmax), a_list))
    plt.grid()
    plt.show()
        
