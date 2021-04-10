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

    # base case: there is only one way to divide N balls among 1 jar
    if jars == 1:
        yield (balls,)
    else:
        for i in range(balls+1):
            for sub in allocations_of(balls-i, jars-1):
                yield (i,) + sub


def product(atoms, length):
    """Enumerates the cartesian product of atoms with itself N times."""
    cache = []
    for i, atom in enumerate(atoms):
        cache.append(atom)
        for js in allocations_of(i, length):
            yield tuple(list(cache[j] for j in js))


def expressible_features(num_days):
    """Enumerates expressible features with support for M sentences over N
    days."""
    cache = []

    def impl():
        rats = nonnegative_rationals()
        sentences = integers(start=1)
        while True:
            # shallow-copy the cache
            cur_cache = [ef for ef in cache]

            # add a constant feature (positive and negative)
            yield Constant(next(rats))
            yield Constant(-next(rats))

            # add a round of price features
            sentence = next(sentences)
            for day in range(num_days):
                yield Price(sentence, day)

            # add reciprocals for each of the base features
            for ftr in cur_cache:
                yield SafeReciprocal(ftr)

            # add sum, product, and max features for each pair of base features
            for a in cur_cache:
                for b in cur_cache:
                    yield Sum(a, b)
                    yield Product(a, b)
                    yield Max(a, b)

    for ftr in impl():
        cache.append(ftr)
        yield ftr


def trading_strategies(num_days, num_sentences):
    """Enumerate trading strategies for day N with support for M
    sentences."""
    features = expressible_features(num_days)
    for st in product(features, repeat=num_sentences):
        yield st


def traders():
    """Enumerate efficiently computable traders. An e.c. trader is a sequence of
    trading strategies in which the n-th element can be computed in time
    polynomial in n.
        
    TODO: implement properly."""
    pass
