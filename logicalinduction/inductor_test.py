from nose.tools import assert_equal, assert_almost_equal, assert_is_instance

import formula
import credence
import sentence
import inductor
import enumerator


def print_formulas(trading_formulas):
    for sentence, formula in trading_formulas.items():
        print(sentence)
        print(formula.tree())
        print()


def test_evaluate():
    world = {1: True, 2: False, 3: False}
    credence_history = credence.History([
        {1: .6},                        # credences after first update
        {1: .7, 2: .4},                 # credences after second update
        {1: .8, 2: .1, 3: .5, 4: .5},
    ])
    trading_formulas = {
        1: formula.Price(1, 2),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the second update
        2: formula.Price(2, 3),   # purchase tokens for sentence 2 in quantity equal to the credence for sentence 2 after the third update
    }
    value = inductor.evaluate(trading_formulas, credence_history, world)
    expected_value = .7 * (1 - .8) + .1 * (0 - .1)
    assert_equal(value, expected_value)


def test_find_credences_trivial():
    credence_history = credence.History([])  # empty history
    trading_formulas = {
        1: formula.Price(1, 1),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the first update
    }
    new_credences = inductor.find_credences(trading_formulas, credence_history, 0.5)
    assert_equal(new_credences[1], 0)


def test_find_credences_single():
    credence_history = credence.History([])  # empty history
    trading_formulas = {
        # purchase sentence 1 in quantity 1 - 3 * credence
        1: formula.Sum(
            formula.Constant(1),
            formula.Product(
                formula.Constant(-3),
                formula.Price(1, 1))),
    }

    new_credences = inductor.find_credences(trading_formulas, credence_history, 1e-5)

    # setting credence to 1/3 yields a trade quantity of zero, which satisfies
    assert_almost_equal(new_credences[1], 1/3)

def test_find_credences_multiple():
    credence_history = credence.History([])  # empty history; we are on the first update
    trading_formulas = {
        # purchase sentence 1 in quantity max(credence-of-sentence-1, credence-of-sentence-2)
        1: formula.Max(
            formula.Price(1, 1),
            formula.Price(2, 1)),
        # purchase sentence 2 in quantity 1 - credence-of-sentence-1 - credence-of-sentence-2
        2: formula.Sum(
            formula.Constant(1),
            formula.Sum(
                formula.Product(
                    formula.Constant(-1),
                    formula.Price(1, 1)),
                formula.Product(
                    formula.Constant(-1),
                    formula.Price(2, 1))))
    }

    new_credences = inductor.find_credences(trading_formulas, credence_history, 1e-5)

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
        phi: formula.Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = inductor.compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert_is_instance(budget_factor, formula.SafeReciprocal)
    
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
    phi = sentence.Atom("ϕ")
    psi = sentence.Atom("Ψ")

    # we are on the first update; our history is all empty
    past_credences = credence.History([])  # no past credences
    past_trading_formulas = []  # no past trading formulas
    past_observations = []  # no past observations

    # we observe psi in our most recent update
    latest_observation = sentence.Disjunction(phi, psi)

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: formula.Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = inductor.compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert_is_instance(budget_factor, formula.SafeReciprocal)

    print()
    print(budget_factor.tree())
    
    # Our world consists of two base facts, phi and psi, and we observed "phi OR psi", so
    # there are three worlds consistent with this observation:
    #   phi=True   psi=True
    #   phi=True   psi=False
    #   phi=False  psi=True
    #
    # Our trading formula says to purchase 10 tokens of phi no matter what. This
    # could cost us between $0 and $10 depending on the credence for phi. The
    # value of these 10 tokens could turn out to be either $0 if phi=False or $10
    # if phi=True:
    #   phi=True   psi=True    -> value of 10 tokens of phi = $10, so net worth between $0 and $10
    #   phi=True   psi=False   -> value of 10 tokens of phi = $10, so net worth between $0 and $10
    #   phi=False  psi=True    -> value of 10 tokens of phi = $0, so net worth between -$10 and $0
    #
    # In the third world, our net worth could drop below our budget for some
    # possible credences, so:
    
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

def test_compute_budget_factor_already_overran_budget():
    phi = sentence.Atom("ϕ")
    psi = sentence.Atom("Ψ")

    # there was one previous observation, which was "phi OR psi"
    past_observations = [sentence.Disjunction(phi, psi)]

    # on our one previous update, our credences were as follows
    past_credences = credence.History([{
        phi: .6,
        psi: .7,
    }])

    # on the previous update we purchased one token of psi
    past_trading_formulas = [{
        psi: formula.Constant(10),
    }]

    # we observe psi in our most recent update
    latest_observation = sentence.Disjunction(phi, psi)

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: formula.Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = inductor.compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    # on our previous update we purchased one token of PSI for $7 without being
    # able to rule out the possibility that PHI could turn out to be false, in
    # which case we would have lost $7, which is more than our budget of $2, so
    # our budget factor should be the constant 0 which eliminates all further
    # trading
    assert_is_instance(budget_factor, formula.Constant)
    assert_equal(budget_factor.k, 0)


def test_combine_trading_algorithms_simple():
    phi = sentence.Atom("ϕ")
    psi = sentence.Atom("Ψ")

    # in this test we are on the first update, so there is one trading
    # algorithm, one observation, and no historical credences
    trading_formula = {phi: formula.Constant(1)}
    trading_histories = [[trading_formula]]
    observation_history = [psi]
    credence_history = credence.History([])

    # create the compound trader, which just has one internal trader
    compound_trader = inductor.combine_trading_algorithms(
        trading_histories,
        observation_history,
        credence_history,
    )

    assert_equal(len(compound_trader), 1)
    assert_is_instance(compound_trader[phi], formula.Sum)
    assert_equal(len(compound_trader[phi].terms), 3)


def test_logical_inductor_simple():
    phi = sentence.Atom("ϕ")
    psi = sentence.Atom("Ψ")

    # create a trading algorithm that purchases 1, 2, 3, ... tokens of phi
    def trading_algorithm(sentence, start=1, step=1):
        for quantity in enumerator.integers(start=start, step=step):
            yield {sentence: formula.Constant(quantity)}

    lia = inductor.LogicalInductor()

    credences = lia.update(sentence.Negation(phi), trading_algorithm(phi, start=1, step=1))
    print(credences)

    credences = lia.update(psi, trading_algorithm(psi, start=-1, step=-1))
    print(credences)

    credences = lia.update(psi, trading_algorithm(psi, start=-1, step=-1))
    print(credences)
