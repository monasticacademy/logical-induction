import itertools
from fractions import Fraction


def integers(start=0, step=1):
    """Enumerates non-negative integers."""
    i = start
    while True:
        yield i
        i += step


def integer_vectors(length, start=0, step=1):
    """Enumerates vectors of integers of the given length."""
    for balls in integers():
        yield from allocations_of(balls, length)


def rationals_between(a, b):
    """Enumerate rationals between the given lower and upper bounds."""
    for denom in integers(start=1):
        for numer in range(0, denom+1):
            yield a + (b-a) * Fraction(numer, denom)


def nonnegative_rationals():
    """Enumerates positive rationals."""
    yield Fraction(0, 1)  # zero is a special case that will not be yielded by the loop below
    for n in integers():
        for denom in range(1, n):
            yield Fraction(n-denom, denom)


def allocations_of(balls, jars):
    """Enumerates the ways to divide N identical balls among K jars.
    Returns a sequence of tuples, each of which contains K integers
    that add up to N."""
    if jars == 1:
        # base case: there is only one way to divide N balls among 1 jar
        yield (balls,)
    else:
        for i in range(balls+1):
            for sub in allocations_of(balls-i, jars-1):
                yield (i,) + sub


def product(xs, length):
    """Enumerates the cartesian product of X with itself N times.
    Unlike itertools.product, this works when X is an infinite sequence."""
    cache = []
    for i, x in enumerate(xs):
        cache.append(x)
        for js in allocations_of(i, length):
            yield tuple(list(cache[j] for j in js))
