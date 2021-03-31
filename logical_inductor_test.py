import trader
import credence
import sentence
import logical_inductor

from nose.tools import assert_equal, assert_almost_equal, assert_is_instance

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
    credence_history = credence.History([])  # empty history; we are on the first update
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


def test_compute_budget_factor_simple():
    phi = sentence.Atom("ϕ")

    # we are on the first update; our history is all empty
    past_credences = credence.History([])  # no past credences
    past_trading_formulas = []  # no past trading formulas
    past_observations = []  # no past observations

    # we observed phi in our most recent update
    latest_observation = phi

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: trader.ConstantFeature(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = logical_inductor.compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert_is_instance(budget_factor, trader.SafeReciprocalFeature)
    
    # our world consists of only one base fact (phi), and we observed phi, so
    # the world where phi=true is only one world propositionally consistent with
    # our observations, and in this world we purchase 10 tokens of phi, which
    # could cost anywhere from $0 to $10 depending on the as-yet-unknown
    # credence for phi, and will have a value of exactly $10 in this world. In
    # no case will the value of our holdings drop below -$2, so we expect a
    # budget factor that evaluates to 1 for all credences in [0, 1].
    assert_equal(budget_factor.evaluate(past_credences.with_next_update({phi: 0.})), 1.)
    assert_equal(budget_factor.evaluate(past_credences.with_next_update({phi: .2})), 1.)
    assert_equal(budget_factor.evaluate(past_credences.with_next_update({phi: .6})), 1.)
    assert_equal(budget_factor.evaluate(past_credences.with_next_update({phi: 1.})), 1.)


def test_compute_budget_factor_two_base_facts():
    #phi = sentence.Atom("ϕ")
    #psi = sentence.Atom("Ψ")
    phi = sentence.Atom("PHI")
    psi = sentence.Atom("PSI")

    # we are on the first update; our history is all empty
    past_credences = credence.History([])  # no past credences
    past_trading_formulas = []  # no past trading formulas
    past_observations = []  # no past observations

    # we observe psi in our most recent update
    latest_observation = sentence.Disjunction(phi, psi)

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: trader.ConstantFeature(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = logical_inductor.compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert_is_instance(budget_factor, trader.SafeReciprocalFeature)

    print()
    print(budget_factor.tree())
    
    # Our world consists of two base facts (phi and psi), and we observed phi|psi, so
    # the three worlds consistent with this observation are:
    #   phi=True   psi=True
    #   phi=True   psi=False
    #   phi=False  psi=True
    #
    # Our trading formula says to purchase 10 tokens of phi no matter what. This
    # could cost us between $0 and $10 depending on the credence for phi. The
    # value of these 10 tokens could turn out to be either $0 or $10 depending
    # on which of the above three worlds we are in: 
    #   phi=True   psi=True    -> value of 10 tokens of phi = $10, so net worth between $0 and $10
    #   phi=True   psi=False   -> value of 10 tokens of phi = $10, so net worth between $0 and $10
    #   phi=False  psi=True    -> value of 10 tokens of phi = $0, so net worth between -$10 and $0
    #
    # In the third world, our net worth could drop below our budget for some
    # possible credences, so...
    
    # if the credence for phi were 1 then in the third world we would end up with a
    # net worth of -$10, so we should multiply our trading volume by 0.2
    assert_almost_equal(budget_factor.evaluate(past_credences.with_next_update({phi: 1.})), .2)

    # if the credence for phi were 0.4 then in the third world we would end up with a
    # net worth of -$4, so we should multiply our trading volume by 0.5
    assert_almost_equal(budget_factor.evaluate(past_credences.with_next_update({phi: .4})), .5)

    # if the credence for phi were 0.2 then in the third world we would end up with a
    # net worth of -$2, which is right on budget, so our scaling factor should be 1
    assert_almost_equal(budget_factor.evaluate(past_credences.with_next_update({phi: .2})), 1.)

    # if the credence for phi were 0 then in the third world we would end up with a
    # net worth of $0, which is above budget, so our scaling factor should be 1
    assert_almost_equal(budget_factor.evaluate(past_credences.with_next_update({phi: 0.})), 1.)
