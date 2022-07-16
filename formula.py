from abc import ABC, abstractmethod

from . import credence


def multiply(xs):
    """Compute the product of the elements of a list, or return None if the list
    is empty."""
    result = None
    for x in xs:
        if result is None:
            result = x
        else:
            result *= x
    return result


def parenthize(formula):
    """Add parentheses around a formula if it is a sum or product formula."""
    if isinstance(formula, (Sum, Product)):
        return "(" + str(formula) + ")"
    else:
        return str(formula)


def maketree(parent_label, children):
    """Construct a multi-line string representing the formula."""
    s = parent_label
    for child in children:
        s += "\n. "
        s += child.tree().replace("\n", "\n. ")
    return s


class Formula(ABC):
    """
    Formula represents a trading formula. It can be evaluated on a set of
    credences, returning a number. It has an upper bounded, which is its
    greatest possible magnitude (assuming credences are between 0 and 1). It has
    a domain, which is the set of sentences upon whose credence it depends.
    """
    @abstractmethod
    def evaluate(self, credence_history):
        """
        Evaluate this formula on the given credence history, returning a number.
        """
        pass

    @abstractmethod
    def bound(self):
        """
        Get an upper bound on the absolute value of this formula for any
        credence history.
        """
        pass

    @abstractmethod
    def domain(self):
        """
        Get the sentences whose price will be used in the
        evaluation of this formula.
        """
        pass

    @abstractmethod
    def tree(self):
        """
        Get a multi-line string representation of this formula.
        """
        pass


class Constant(Formula):
    """
    Represents a trading formula that is a constant.
    """
    def __init__(self, k):
        self.k = k

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return self.k

    def bound(self):
        return abs(self.k)

    def domain(self):
        return set()

    def tree(self):
        return "Constant({})".format(str(self.k))

    def __str__(self):
        return str(self.k)

    def __repr__(self):
        return str(self)


class Price(Formula):
    """
    Represents a trading formula that looks up the price for a given sentence on
    a given day.
    """
    def __init__(self, sentence, day: int):
        assert(day >= 1)  # day indices are 1-based
        self.sentence = sentence
        self.day = day

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return credence_history.lookup(self.sentence, self.day)

    def bound(self):
        return 1   # because credences are always between 0 and 1

    def domain(self):
        return {self.sentence}

    def tree(self):
        return "Price({}, {})".format(self.sentence, self.day)

    def __str__(self):
        return "price({}, {})".format(self.sentence, self.day)

    def __repr__(self):
        return str(self)


class Sum(Formula):
    """
    Represents a trading formula that is the sum of some other formulas."""
    def __init__(self, *terms):
        self.terms = list(terms)

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return sum(term.evaluate(credence_history) for term in self.terms)

    def bound(self):
        return sum(term.bound() for term in self.terms)

    def domain(self):
        return set.union(*(term.domain() for term in self.terms))

    def tree(self):
        return maketree("Sum", self.terms)

    def __str__(self):
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            return " + ".join(parenthize(term) for term in self.terms)

    def __repr__(self):
        return str(self)


class Product(Formula):
    """
    Represents a trading formula that is the product of some other formulas.
    """
    def __init__(self, *terms):
        self.terms = list(terms)

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return multiply(term.evaluate(credence_history) for term in self.terms)

    def bound(self):
        # bounds are always >= 0 so we can multiply them safely
        return multiply(term.bound() for term in self.terms)

    def domain(self):
        return set.union(*(term.domain() for term in self.terms))

    def tree(self):
        return maketree("Product", self.terms)

    def __str__(self):
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            return " * ".join(parenthize(term) for term in self.terms)

    def __repr__(self):
        return str(self)


class Max(Formula):
    """
    Represents a trading formula that is the max of some other formulas.
    """
    def __init__(self, *terms):
        self.terms = list(terms)

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return max(term.evaluate(credence_history) for term in self.terms)

    def bound(self):
        return max(term.bound() for term in self.terms)

    def domain(self):
        return set.union(*(term.domain() for term in self.terms))

    def tree(self):
        return maketree("Max", self.terms)

    def __str__(self):
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            s = ", ".join(str(term) for term in self.terms)
            return "max({})".format(s)

    def __repr__(self):
        return str(self)


class Min(Formula):
    """
    Represents a trading formula that is the min of some other formulas.
    """
    def __init__(self, *terms):
        self.terms = list(terms)

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return min(term.evaluate(credence_history) for term in self.terms)

    def bound(self):
        return min(term.bound() for term in self.terms)

    def domain(self):
        return set.union(*(term.domain() for term in self.terms))

    def tree(self):
        return maketree("Min", self.terms)

    def __str__(self):
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            s = ", ".join(str(term) for term in self.terms)
            return "min({})".format(s)

    def __repr__(self):
        return str(self)


class SafeReciprocal(Formula):
    """Represents an expressible feature: 1 / max(1, x)."""
    def __init__(self, x):
        self.x = x

    def evaluate(self, credence_history):
        assert isinstance(credence_history, credence.History)
        return 1. / max(1., self.x.evaluate(credence_history))

    def bound(self):
        return 1.  # the denominator is always >= 1, so the result is always <= 1

    def domain(self):
        return self.x.domain()

    def tree(self):
        return maketree("SafeReciprocal", [self.x])

    def __str__(self):
        return "safe_reciprocal({})".format(str(self.x))

    def __repr__(self):
        return str(self)
