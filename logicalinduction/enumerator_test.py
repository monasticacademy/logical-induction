import itertools

from .enumerator import integer_vectors, product


def test_integer_vectors():
    it = integer_vectors(3)
    assert next(it) == (0, 0, 0)
    assert next(it) == (0, 0, 1)
    assert next(it) == (0, 1, 0)
    assert next(it) == (1, 0, 0)
    assert next(it) == (0, 0, 2)
    assert next(it) == (0, 1, 1)
    assert next(it) == (0, 2, 0)
    assert next(it) == (1, 0, 1)
    assert next(it) == (1, 1, 0)
    assert next(it) == (2, 0, 0)
    assert next(it) == (0, 0, 3)


def test_product():
    it = product(itertools.cycle('abcd'), 2)
    assert ''.join(next(it)) == 'aa'
    assert ''.join(next(it)) == 'ab'
    assert ''.join(next(it)) == 'ba'
    assert ''.join(next(it)) == 'ac'
    assert ''.join(next(it)) == 'bb'
    assert ''.join(next(it)) == 'ca'
    assert ''.join(next(it)) == 'ad'
    assert ''.join(next(it)) == 'bc'
    assert ''.join(next(it)) == 'cb'
    assert ''.join(next(it)) == 'da'
