

def parethize(sentence):
    """Add parentheses around a sentence unless it is an atom."""
    if isinstance(sentence, Atom):
        return str(sentence)
    else:
        return "(" + str(sentence) + ")"


class Sentence(object):
    """
    A sentence is a combination of atoms and logical connectives that evaluates
    to true or false in a given world.
    """
    def evaluate(self, world):
        raise NotImplemented


class Atom(Sentence):
    """
    An atom is a base fact that is not further reducible into components joined
    by logical connectives. It has a label, which is a string that humans may
    use to identify it.
    """
    def __init__(self, label):
        self.label = label

    def evaluate(self, world):
        return world[self.label]

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
    
    def evaluate(self, world):
        return not self.inner.evaluate(world)
    
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
    
    def evaluate(self, world):
        return any(term.evaluate(world) for term in self.disjunct)

    def atoms(self):
        return set.union(*(term.atoms() for term in self.disjuncts))

    def __str__(self):
        return " ∨ ".join(parenthize(term) for term in self.disjuncts)

    def __repr__(self):
        return str(self)


class Conjunction(Sentence):
    """
    A conjunction is true if all of its sub-sentences are true.
    """
    def __init__(self, *conjuncts):
        self.conjuncts = conjuncts
    
    def evaluate(self, world):
        return all(term.evaluate(world) for term in self.conjuncts)

    def atoms(self):
        return set.union(*(term.atoms() for term in self.conjuncts))

    def __str__(self):
        return " ∧ ".join(parenthize(term) for term in self.conjuncts)

    def __repr__(self):
        return str(self)


class Implication(Sentence):
    """
    An implication is true unless its antecedent is true and consequent is false
    """
    def __init__(self, antecedent, consequent):
        self.antecedent = antecedent
        self.consequent = consequent
    
    def evaluate(self, world):
        return not self.antecedent.evaluate(world) or self.consequent.evaluate(world)

    def atoms(self):
        return set.union(self.antecedent.atoms(), self.consequent.atoms())
    
    def __str__(self):
        return "{} → {}".format(str(self.antecedent), str(self.consequent))

    def __repr__(self):
        return str(self)
