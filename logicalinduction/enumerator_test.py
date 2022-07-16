import itertools
from nose.tools import assert_equal

import enumerator


def test_integer_vectors():
    it = enumerator.integer_vectors(3)
    assert_equal(next(it), (0, 0, 0))
    assert_equal(next(it), (0, 0, 1))
    assert_equal(next(it), (0, 1, 0))
    assert_equal(next(it), (1, 0, 0))
    assert_equal(next(it), (0, 0, 2))
    assert_equal(next(it), (0, 1, 1))
    assert_equal(next(it), (0, 2, 0))
    assert_equal(next(it), (1, 0, 1))
    assert_equal(next(it), (1, 1, 0))
    assert_equal(next(it), (2, 0, 0))
    assert_equal(next(it), (0, 0, 3))


def test_product():
    it = enumerator.product(itertools.cycle('abcd'), 2)
    assert_equal(''.join(next(it)), 'aa')
    assert_equal(''.join(next(it)), 'ab')
    assert_equal(''.join(next(it)), 'ba')
    assert_equal(''.join(next(it)), 'ac')
    assert_equal(''.join(next(it)), 'bb')
    assert_equal(''.join(next(it)), 'ca')
    assert_equal(''.join(next(it)), 'ad')
    assert_equal(''.join(next(it)), 'bc')
    assert_equal(''.join(next(it)), 'cb')
    assert_equal(''.join(next(it)), 'da')
