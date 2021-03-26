

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
        return self.a.evaluate(market) + self.b.evaluate(market)

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
        return self.a.evaluate(market) * self.b.evaluate(market)

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
        return max(self.a.evaluate(market), self.b.evaluate(market))

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
        return 1. / max(1., self.a.evaluate(market))

    def bound(self):
        return 1.  # the denominator is always >= 1, so the result is always <= 1

    def domain(self):
        return self.a.domain()

    def __str__(self):
        return "safe_reciprocal({})".format(str(self.a))

    def __repr__(self):
        return str(self)
