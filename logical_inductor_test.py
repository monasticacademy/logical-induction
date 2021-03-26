import credence
import trader
import logical_inductor

from nose.tools import assert_equal, assert_almost_equal

def test_evaluate():
    world = {1: True, 2: False, 3: False}
    credence_history = credence.History([
        {1: .6},                        # credences after first update
        {1: .7, 2: .4},                 # credences after second update
        {1: .8, 2: .1, 3: .5, 4: .5},
    ])
    trading_formulas = {
        1: trader.PriceFeature(1, 2),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the second update
        2: trader.PriceFeature(2, 3),   # purchase tokens for sentence 2 in quantity equal to the credence for sentence 2 after the third update
    }
    value = logical_inductor.evaluate(trading_formulas, credence_history, world)
    expected_value = .7 * (1 - .8) + .1 * (0 - .1)
    assert_equal(value, expected_value)


def test_find_credences_trivial():
    credence_history = credence.History([])  # empty history
    trading_formulas = {
        1: trader.PriceFeature(1, 1),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the first update
    }
    new_credences = logical_inductor.find_credences(trading_formulas, credence_history, 0.5)
    assert_equal(new_credences[1], 0)


def test_find_credences_single():
    credence_history = credence.History([])  # empty history
    trading_formulas = {
        # purchase sentence 1 in quantity 1 - 3 * credence
        1: trader.SumFeature(
            trader.ConstantFeature(1),
            trader.ProductFeature(
                trader.ConstantFeature(-3),
                trader.PriceFeature(1, 1))),
    }

    new_credences = logical_inductor.find_credences(trading_formulas, credence_history, 1e-5)

    # setting credence to 1/3 yields a trade quantity of zero, which satisfies
    assert_almost_equal(new_credences[1], 1/3)

def test_find_credences_multiple():
    credence_history = credence.History([])  # empty history
    trading_formulas = {
        # purchase sentence 1 in quantity max(credence-of-sentence-1, credence-of-sentence-2)
        1: trader.MaxFeature(
            trader.PriceFeature(1, 1),
            trader.PriceFeature(2, 1)),
        # purchase sentence 2 in quantity 1 - credence-of-sentence-1 - credence-of-sentence-2
        2: trader.SumFeature(
            trader.ConstantFeature(1),
            trader.SumFeature(
                trader.ProductFeature(
                    trader.ConstantFeature(-1),
                    trader.PriceFeature(1, 1)),
                trader.ProductFeature(
                    trader.ConstantFeature(-1),
                    trader.PriceFeature(2, 1))))
    }

    new_credences = logical_inductor.find_credences(trading_formulas, credence_history, 1e-5)

    # setting credence[1] to 1 and credence[2] to 0 satisfies the conditions
    assert_almost_equal(new_credences[1], 1)
    assert_almost_equal(new_credences[2], 0)
