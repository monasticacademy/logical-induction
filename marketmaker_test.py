import credence
import trader
import marketmaker

from nose.tools import assert_equal

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
    value = marketmaker.evaluate(trading_formulas, credence_history, world)
    expected_value = .7 * (1 - .8) + .1 * (0 - .1)
    assert_equal(value, expected_value)