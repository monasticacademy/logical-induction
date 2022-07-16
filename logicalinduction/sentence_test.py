from nose.tools import assert_equal, assert_true, assert_false

from sentence import Atom, Negation, Disjunction, Conjunction

def test_atom():
    world = {"s1": True, "s2": False}
    s1 = Atom("s1")
    s2 = Atom("s2")
    assert_equal(s1.atoms(), {"s1"})
    assert_true(s1.evaluate(world))
    assert_false(s2.evaluate(world))


def test_negation():
    world = {"s1": True, "s2": False}
    s1 = Negation(Atom("s1"))
    s2 = Negation(Atom("s2"))
    assert_equal(s1.atoms(), {"s1"})
    assert_false(s1.evaluate(world))
    assert_true(s2.evaluate(world))


def test_conjunction():
    world = {"s1": True, "s2": False}
    s1 = Atom("s1")
    s2 = Atom("s2")
    s = Conjunction(s1, s2)
    assert_equal(s.atoms(), {"s1", "s2"})
    assert_false(s.evaluate(world))

