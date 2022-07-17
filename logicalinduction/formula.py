from abc import ABC, abstractmethod
from operator import mul
from typing import Iterator, Protocol, Iterable
from functools import reduce
from fractions import Fraction

from .sentence import Sentence
from .credence import History


class Number(Protocol):
    def __abs__(self) -> 'Number':
        ...
    def __mul__(self, Number) -> 'Number':
        ...
    def __add__(self, Number) -> 'Number':
        ...
    def __lt__(self, Number) -> bool:
        ...
    def __gt__(self, Number) -> bool:
        ...
    def __truediv__(self, Number) -> 'Number':
        ...
    def __rtruediv__(self, Number) -> 'Number':
        ...


def multiply(xs: Iterator[Number]) -> Number:
    """Compute the product of the elements of a list, or return None if the list
    is empty."""
    return reduce(mul, xs)


def parenthize(formula: 'Formula'):
    """Add parentheses around a formula if it is a sum or product formula."""
    if isinstance(formula, (Sum, Product)):
        return "(" + str(formula) + ")"
    else:
        return str(formula)


def maketree(parent_label: str, children : Iterable['Formula']) -> str:
    """Construct a multi-line string representing the formula."""
    s = parent_label
    for child in children:
        s += "\n. "
        s += child.tree().replace("\n", "\n. ")
    return s


class Formula(ABC):
    """
    Represents a trading formula. It can be evaluated on a set of
    credences, returning a number. It has an upper bounded, which is its
    greatest possible magnitude (assuming credences are between 0 and 1). It has
    a domain, which is the set of sentences upon whose credence it depends.
    """
    @abstractmethod
    def evaluate(self, credence_history: History) -> Number:
        """
        Evaluate this formula on the given credence history, returning a number.
        """
        pass

    @abstractmethod
    def bound(self) -> Number:
        """
        Get an upper bound on the absolute value of this formula for any
        credence history.
        """
        pass

    @abstractmethod
    def domain(self) -> set[Sentence]:
        """
        Get the sentences whose price will be used in the
        evaluation of this formula.
        """
        pass

    @abstractmethod
    def tree(self) -> str:
        """
        Get a multi-line string representation of this formula.
        """
        pass


class Constant(Formula):
    """
    Represents a constant trading formula.
    """
    def __init__(self, k: Number):
        self.k = k

    def evaluate(self, credence_history: History) -> Number:
        return self.k

    def bound(self) -> Number:
        return abs(self.k)

    def domain(self) -> set[Sentence]:
        return set()

    def tree(self) -> str:
        return "Constant({})".format(str(self.k))

    def __str__(self) -> str:
        return str(self.k)

    def __repr__(self) -> str:
        return str(self)


class Price(Formula):
    """
    Looks up the price for a given sentence on a given update.
    """
    def __init__(self, sentence: Sentence, update_index: int):
        assert(update_index >= 1)  # indices are 1-based
        self.sentence = sentence
        self.update_index = update_index

    def evaluate(self, credence_history: History) -> Number:
        return credence_history.lookup(self.sentence, self.update_index)

    def bound(self) -> Number:
        return Fraction(1, 1)   # because credences are always between 0 and 1

    def domain(self) -> set[Sentence]:
        return {self.sentence}

    def tree(self) -> str:
        return "Price({}, {})".format(self.sentence, self.update_index)

    def __str__(self) -> str:
        return "price({}, {})".format(self.sentence, self.update_index)

    def __repr__(self) -> str:
        return str(self)


class Sum(Formula):
    """
    Represents a sum of trading formulas.
    """
    def __init__(self, *terms: Formula):
        self.terms = list(terms)

    def evaluate(self, credence_history: History) -> Number:
        return sum(term.evaluate(credence_history) for term in self.terms)

    def bound(self) -> Number:
        return sum(term.bound() for term in self.terms)

    def domain(self) -> set[Sentence]:
        return set.union(*(term.domain() for term in self.terms))

    def tree(self) -> str:
        return maketree("Sum", self.terms)

    def __str__(self) -> str:
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            return " + ".join(parenthize(term) for term in self.terms)

    def __repr__(self) -> str:
        return str(self)


class Product(Formula):
    """
    Represents a product of trading formulas.
    """
    def __init__(self, *terms: Formula):
        self.terms = list(terms)

    def evaluate(self, credence_history: History) -> Number:
        return multiply(term.evaluate(credence_history) for term in self.terms)

    def bound(self) -> Number:
        # bounds are always >= 0 so we can multiply them safely
        return multiply(term.bound() for term in self.terms)

    def domain(self) -> set[Sentence]:
        return set.union(*(term.domain() for term in self.terms))

    def tree(self) -> str:
        return maketree("Product", self.terms)

    def __str__(self) -> str:
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            return " * ".join(parenthize(term) for term in self.terms)

    def __repr__(self) -> str:
        return str(self)


class Max(Formula):
    """
    Represents a max over trading formulas.
    """
    def __init__(self, *terms: Formula):
        self.terms = list(terms)

    def evaluate(self, credence_history: History) -> Number:
        return max(term.evaluate(credence_history) for term in self.terms)

    def bound(self) -> Number:
        return max(term.bound() for term in self.terms)

    def domain(self) -> set[Sentence]:
        return set.union(*(term.domain() for term in self.terms))

    def tree(self) -> str:
        return maketree("Max", self.terms)

    def __str__(self) -> str:
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            s = ", ".join(str(term) for term in self.terms)
            return "max({})".format(s)

    def __repr__(self) -> str:
        return str(self)


class Min(Formula):
    """
    Represents a min over trading formulas.
    """
    def __init__(self, *terms):
        self.terms = list(terms)

    def evaluate(self, credence_history: History) -> Number:
        return min(term.evaluate(credence_history) for term in self.terms)

    def bound(self) -> Number:
        return min(term.bound() for term in self.terms)

    def domain(self) -> set[Sentence]:
        return set.union(*(term.domain() for term in self.terms))

    def tree(self) -> str:
        return maketree("Min", self.terms)

    def __str__(self) -> str:
        # avoid unnecessary parentheses if there is only one term
        if len(self.terms) == 1:
            return str(self.terms[0])
        else:
            s = ", ".join(str(term) for term in self.terms)
            return "min({})".format(s)

    def __repr__(self) -> str:
        return str(self)


class SafeReciprocal(Formula):
    """
    Represents 1 / max(1, x) where x is a trading formula.
    """
    def __init__(self, x: Formula):
        self.x = x

    def evaluate(self, credence_history: History) -> Number:
        return 1. / max(1., self.x.evaluate(credence_history))

    def bound(self) -> Number:
        return 1.  # the denominator is always >= 1, so the result is always <= 1

    def domain(self) -> set[Sentence]:
        return self.x.domain()

    def tree(self) -> str:
        return maketree("SafeReciprocal", [self.x])

    def __str__(self) -> str:
        return "safe_reciprocal({})".format(str(self.x))

    def __repr__(self) -> str:
        return str(self)
