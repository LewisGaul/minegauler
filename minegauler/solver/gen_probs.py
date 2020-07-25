# July 2020, Lewis Gaul

"""
Generate probabilities.

"""

__all__ = ("combs", "log_combs", "prob")

import functools
from math import exp
from math import factorial as fac
from math import log


# @@@ Move this to testing.
# Cache of combination calculations.
# This mapping is structured as follows:
#  {
#    <nr_cells>: {
#      (<per_cell>, <nr_mines>): <combinations>,
#      ...
#    },
#    ...
#  }
_mult_combs = {
    2: {(2, 3): 6, (2, 4): 6, (3, 4): 14, (3, 5): 20, (3, 6): 20},
    3: {
        (2, 3): 24,
        (2, 4): 54,
        (2, 5): 90,
        (2, 6): 90,
        (3, 4): 78,
        (3, 5): 210,
        (3, 6): 510,
        (3, 7): 1050,
        (3, 8): 1680,
        (3, 9): 1680,
    },
    4: {
        (2, 3): 60,
        (2, 4): 204,
        (2, 5): 600,
        (2, 6): 1440,
        (2, 7): 2520,
        (2, 8): 2520,
        (3, 4): 252,
        (3, 5): 960,
        (3, 6): 3480,
        (3, 7): 11760,
        (3, 8): 28120,
        (3, 9): 67200,
        (3, 10): 218400,
        (3, 11): 369600,
        (3, 12): 369600,
    },
    5: {
        (2, 3): 120,
        (2, 4): 540,
        (2, 5): 2220,
        (2, 6): 8100,
        (2, 7): 25200,
        (2, 8): 63000,
        (2, 9): 113400,
        (2, 10): 113400,
        (3, 4): 620,
        (3, 5): 3020,
        (3, 6): 14300,
        (3, 7): 65100,
    },
}


@functools.lru_cache(1000)
def combs(s: int, m: int, xmax: int = 1) -> int:
    if m > s * xmax:
        return 0
    elif s == 1:
        return 1
    elif xmax == 1:
        return fac(s) // fac(s - m)
    elif xmax >= m:
        return s ** m
    else:
        return _find_combs(s, m, xmax)


@functools.lru_cache(1000)
def log_combs(s: int, m: int, xmax: int = 1) -> float:
    if m > s * xmax:
        raise ValueError("Too many mines")
    elif s == 1:
        return 0
    elif xmax == 1:
        return log(fac(s) // fac(s - m))
    elif xmax >= m:
        return m * log(s)
    else:
        return log(_find_combs(s, m, xmax))


def prob(s: int, m: int, xmax: int = 1) -> float:
    """
    Calculate the probability a cell contains a mine in a group of size s
    containing m mines and with max per cell of xmax.
    """
    if m > s * xmax:
        return 0
    if xmax == 1:
        return m / s
    elif xmax >= m:
        return 1 - (1 - 1 / s) ** m
    elif m > xmax * (s - 1):
        return 1
    else:
        return 1 - exp(log_combs(s - 1, m, xmax) - log_combs(s, m, xmax))


def _find_combs(s: int, m: int, xmax: int) -> int:
    cfgs = [[0] * s]
    # cfgs = [(1,) * min(m,s) + (0,) * max(0,s-m)]
    # i = m
    # t = tm.time()
    ##    while i > 0:
    ##        new_cfgs = []
    ##        for c in cfgs:
    ##            for j in uniquify(c):
    ##                if j >= xmax:
    ##                    break
    ##                c1 = list(c)
    ##                c1[c.index(j)] += 1
    ##                new_cfgs.append(tuple(c1))
    ##        cfgs = uniquify(new_cfgs)
    ##        i -= 1
    end_cfgs = []
    for i in range(s):
        new_cfgs = []
        # print cfgs
        for c in cfgs:
            for j in range((m - sum(c) - 1) // (s - i) + 1, min(xmax, m - sum(c)) + 1):
                if i != 0 and j > c[i - 1]:
                    break
                c1 = c[:]
                c1[i] = j
                if sum(c1) == m:
                    end_cfgs.append(tuple(c1))
                else:
                    new_cfgs.append(c1)
        cfgs = new_cfgs[:]
    # print "Time taken:", tm.time() - t, s, m
    cfgs = sorted(end_cfgs, reverse=True)
    tot = 0
    for c in cfgs:
        combs = fac(s) * fac(m)
        for i in sorted(set(c)):
            combs //= fac(c.count(i))
            combs //= fac(i) ** c.count(i)
        tot += combs
    return tot
