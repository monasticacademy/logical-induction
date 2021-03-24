import copy
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


class ConstantFeature(object):
    """Represents an expressible feature that is a constant."""
    def __init__(self, k):
        self.k = k

    def evaluate(self, market):
        return self.k

    def bound(self):
        return abs(self.k)

    def domain(self):
        return set()

    def __str__(self):
        return str(self.k)

    def __repr__(self):
        return str(self)


class PriceFeature(object):
    """Represents an expressible feature that looks up the price for a
    given sentence on a given day."""
    def __init__(self, sentence, day):
        self.sentence = sentence
        self.day = day

    def evaluate(self, market):
        return market.lookup(self.sentence, self.day)

    def bound(self):
        return 1.   # because markets are constrained to [0,1] prices

    def domain(self):
        return {self.sentence}

    def __str__(self):
        return "price({}, {})".format(self.sentence, self.day)

    def __repr__(self):
        return str(self)


class SumFeature(object):
    """Represents an expressible feature that is the sum of two
    features."""
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def evaluate(self, market):
        return self.a.evalaute(market) + self.b.evaluate(market)

    def bound(self):
        return self.a.bound() + self.b.bound()

    def domain(self):
        return self.a.domain().union(self.b.domain())

    def __str__(self):
        s = "{} + {}".format(str(self.a), str(self.b))
        # we only need parentheses if one of the underlying features
        # has a precedence higher than us, which in this simple
        # language is only a product feature
        if isinstance(self.a, ProductFeature) or isinstance(self.b, ProductFeature):
            s = "(" + s + ")"
        return s

    def __repr__(self):
        return str(self)


class ProductFeature(object):
    """Represents an expressible feature that is the product of two
    features."""
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def evaluate(self, market):
        return self.a.evalaute(market) * self.b.evaluate(market)

    def bound(self):
        return self.a.bound() * self.b.bound()

    def domain(self):
        return self.a.domain().union(self.b.domain())

    def __str__(self):
        return "{} * {}".format(str(self.a), str(self.b))

    def __repr__(self):
        return str(self)


class MaxFeature(object):
    """Represents an expressible feature that is the max of two
    features."""
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def evaluate(self, market):
        return max(self.a.evalaute(market) + self.b.evaluate(market))

    def bound(self):
        return max(self.a.bound(), self.b.bound())

    def domain(self):
        return self.a.domain().union(self.b.domain())

    def __str__(self):
        return "max({}, {})".format(str(self.a), str(self.b))

    def __repr__(self):
        return str(self)


class SafeReciprocalFeature(object):
    """Represents an expressible feature: 1 / max(1, x)."""
    def __init__(self, a):
        self.a = a

    def evaluate(self, market):
        return 1. / max(1., self.a.evalaute(market))

    def bound(self):
        return 1.  # the denominator is always >= 1, so the result is always <= 1

    def domain(self):
        return self.a.domain()

    def __str__(self):
        return "safe_reciprocal({})".format(str(self.a))

    def __repr__(self):
        return str(self)

            
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
            yield ConstantFeature(next(rats))
            yield ConstantFeature(-next(rats))

            # add a round of price features
            sentence = next(sentences)
            for day in range(num_days):
                yield PriceFeature(sentence, day)

            # add reciprocals for each of the base features
            for ftr in cur_cache:
                yield SafeReciprocalFeature(ftr)

            # add sum, product, and max features for each pair of base features
            for a in cur_cache:
                for b in cur_cache:
                    yield SumFeature(a, b)
                    yield ProductFeature(a, b)
                    yield MaxFeature(a, b)

    for ftr in impl():
        cache.append(ftr)
        yield ftr


def trading_strategies(num_days, num_sentences):
    """Enumerate trading strategies for day N with support for M
    sentences."""
    features = expressible_features(num_days)
    for st in itertools.product(features, repeat=num_sentences):
        yield st


def traders():
    """Enumerate efficiently computable traders. An e.c. trader is a sequence of
    trading strategies in which the n-th element can be computed in time
    polynomial in n.
    
    For now we just return constant trading strategies.
    
    TODO: implement properly."""
    pass
        
def main_allocations():
    for t in allocations_of(3, 3):
        print(t)


def main_rationals():
    for q in itertools.islice(nonnegative_rationals(), 0, 20):
        print(q)

        
def main_sequences_of():
    for seq in itertools.islice(sequences_of(integers(0)), 0, 100):
        print(list(itertools.islice(seq, 0, 10)))


def main_expressible_features():
    for ftr in itertools.islice(expressible_features(3), 0, 500):
        print(ftr)


def main():
    #main_rationals()
    main_expressible_features()
    #main_sequences_of()

        
if __name__ == "__main__":
    main()
