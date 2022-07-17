from .sentence import Atom, Negation, Conjunction

def test_atom():
    world = {"s1": True, "s2": False}
    s1 = Atom("s1")
    s2 = Atom("s2")
    assert s1.atoms() == {"s1"}
    assert s1.evaluate(world)
    assert not s2.evaluate(world)


def test_negation():
    world = {"s1": True, "s2": False}
    s1 = Negation(Atom("s1"))
    s2 = Negation(Atom("s2"))
    assert s1.atoms() == {"s1"}
    assert not s1.evaluate(world)
    assert s2.evaluate(world)


def test_conjunction():
    world = {"s1": True, "s2": False}
    s1 = Atom("s1")
    s2 = Atom("s2")
    s = Conjunction(s1, s2)
    assert s.atoms() == {"s1", "s2"}
    assert not s.evaluate(world)
