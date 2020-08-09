from fractions import Fraction


def prefix(n, seq):
    """Returns the first N elements of seq."""
    for i in range(n):
        yield next(seq)


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


def integers(start=0, step=1):
    """Enumerates positive integers."""
    i = start
    while True:
        yield i
        i += step

        
def sequences_of(atoms):
    """Enumerates all possible sequences of the elements in atoms (which
    can itself be a never-ending generator)."""
    cache = [next(atoms)]

    def sequence_for(allocation):
        for i in allocation:
            yield cache[i]
        while True:
            yield cache[0]

    # yield the initial "zero" sequence
    yield sequence_for(())

    # yield the rest of the sequences
    for i in integers(1):
        cache.append(next(atoms))
        for allocation in allocations_of(i, i):
            yield sequence_for(allocation)


class ConstantFeature(object):
    """Represents an expressible feature that is a constant."""
    def __init__(self, k):
        self.k = k

    def evaluate(self, market):
        return self.k

    def bound(self):
        return abs(self.k)

    def __str__(self):
        return str(self.k)


class PriceFeature(object):
    """Represents an expressible feature that looks up the price for a
    given sentence on a given day."""
    def __init__(self, sentence, day):
        self.sentence = sentence
        self.day = day

    def evaluate(self, market):
        return market.price(self.sentence, self.day)

    def bound(self):
        return 1.   # because markets are constrained to [0,1] prices

    def __str__(self):
        return "price({}, {})".format(self.sentence, self.day)


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

    def __str__(self):
        return "{} + {})".format(str(self.a), str(self.b))


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

    def __str__(self):
        return "{} * {})".format(str(self.a), str(self.b))


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

    def __str__(self):
        return "max({}, {})".format(str(self.a), str(self.b))


class SafeReciprocalFeature(object):
    """Represents an expressible feature: 1 / max(1, x)."""
    def __init__(self, a):
        self.a = a

    def evaluate(self, market):
        return 1. / max(1., self.a.evalaute(market))

    def bound(self):
        return 1.  # the denominator is always >= 1, so the result is always <= 1

    def __str__(self):
        return "safe_reciprocal({})".format(str(self.a))

            
def expressible_features(num_sentences, num_days):
    yield MaxFeature(ConstantFeature(Fraction(4, 5)), PriceFeature(3, 6))


def main_allocations():
    for t in allocations_of(3, 3):
        print(t)


def main_sequences_of():
    for seq in prefix(100, sequences_of(integers(0))):
        print(list(prefix(10, seq)))


def main_expressible_features():
    for ftr in prefix(5, expressible_features(3, 4)):
        print(ftr)


def main():
    main_expressible_features()
    #main_sequences_of()

        
if __name__ == "__main__":
    main()
