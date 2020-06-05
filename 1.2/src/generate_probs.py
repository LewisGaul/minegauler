from math import factorial as fac

mult_combs = {
    2: {
        (2, 3): 6, (2, 4): 6,
        (3, 4): 14, (3, 5): 20, (3, 6): 20
    },
    3: {
        (2, 3): 24, (2, 4): 54, (2, 5): 90, (2, 6): 90,
        (3, 4): 78, (3, 5): 210, (3, 6): 510, (3, 7): 1050, (3, 8): 1680,
        (3, 9): 1680
    },
    4: {
        (2, 3): 60, (2, 4): 204, (2, 5): 600, (2, 6): 1440, (2, 7): 2520,
        (2, 8): 2520,
        (3, 4): 252, (3, 5): 960, (3, 6): 3480, (3, 7): 11760, (3, 8): 28120,
        (3, 9): 67200, (3, 10): 218400, (3, 11): 369600, (3, 12): 369600
    },
    5: {
        (2, 3): 120, (2, 4): 540, (2, 5): 2220, (2, 6): 8100, (2, 7): 25200,
        (2, 8): 63000, (2, 9): 113400, (2, 10): 113400,
        (3, 4): 620, (3, 5): 3020, (3, 6): 14300, (3, 7): 65100
    }
}

def combs(s, m, xmax=1):
    if xmax == 1:
        return fac(s)/fac(s - m)
    elif xmax >= m:
        return s**m
    elif m > s*xmax:
        return 0
    else:
        try:
            return mult_combs[s][(xmax, m)]
        except KeyError:
            raise ValueError(
                "Missing entry for s={}, xmax={}, m={}".format(s, xmax, m))

def prob(s, m, xmax=1):
    """
    Calculate the probability a cell contains a mine in a group of size s
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
        return 1 - float(combs(s-1, m, xmax))/combs(s, m, xmax)