from abc import ABC, abstractmethod


def parenthize(sentence):
    """Add parentheses around a sentence unless it is an atom."""
    if isinstance(sentence, Atom):
        return str(sentence)
    else:
        return "(" + str(sentence) + ")"


class Sentence(ABC):
    """
    A sentence is a combination of atoms and logical connectives that evaluates
    to true or false over a given set of base facts.
    """
    @abstractmethod
    def evaluate(self, base_facts):
        pass


class Atom(Sentence):
    """
    An atom is a base fact that is not further reducible into components joined
    by logical connectives. It has a label, which is a string that humans may
    use to identify it.
    """
    def __init__(self, label):
        self.label = label

    def evaluate(self, base_facts):
        return base_facts[self.label]

    def atoms(self):
        return {self.label}
    
    def __str__(self):
        return self.label

    def __repr__(self):
        return str(self)


class Negation(Sentence):
    """
    A negation is true if its sub-sentence is false.
    """
    def __init__(self, inner):
        self.inner = inner
    
    def evaluate(self, base_facts):
        return not self.inner.evaluate(base_facts)
    
    def atoms(self):
        return self.inner.atoms()
    
    def __str__(self):
        return "¬" + str(self.inner)
    
    def __repr__(self):
        return str(self)


class Disjunction(Sentence):
    """
    A disjunction is true if any of its sub-sentences are true.
    """
    def __init__(self, *disjuncts):
        self.disjuncts = disjuncts
    
    def evaluate(self, base_facts):
        return any(term.evaluate(base_facts) for term in self.disjuncts)

    def atoms(self):
        return set.union(*(term.atoms() for term in self.disjuncts))

    def __str__(self):
        return " | ".join(parenthize(term) for term in self.disjuncts)

    def __repr__(self):
        return str(self)


class Conjunction(Sentence):
    """
    A conjunction is true if all of its sub-sentences are true.
    """
    def __init__(self, *conjuncts):
        self.conjuncts = conjuncts
    
    def evaluate(self, base_facts):
        return all(term.evaluate(base_facts) for term in self.conjuncts)

    def atoms(self):
        return set.union(*(term.atoms() for term in self.conjuncts))

    def __str__(self):
        return " & ".join(parenthize(term) for term in self.conjuncts)

    def __repr__(self):
        return str(self)


class Implication(Sentence):
    """
    An implication is true unless its antecedent is true and consequent is false
    """
    def __init__(self, antecedent, consequent):
        self.antecedent = antecedent
        self.consequent = consequent
    
    def evaluate(self, base_facts):
        return not self.antecedent.evaluate(base_facts) or self.consequent.evaluate(base_facts)

    def atoms(self):
        return set.union(self.antecedent.atoms(), self.consequent.atoms())
    
    def __str__(self):
        return "{} → {}".format(str(self.antecedent), str(self.consequent))

    def __repr__(self):
        return str(self)


class Iff(Sentence):
    """
    An iff is true if its left and right sides have the same truth value
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def evaluate(self, base_facts):
        return self.left.evaluate(base_facts) == self.right.evaluate(base_facts)

    def atoms(self):
        return set.union(self.left.atoms(), self.right.atoms())
    
    def __str__(self):
        return "{} ⟷ {}".format(str(self.left), str(self.right))

    def __repr__(self):
        return str(self)
