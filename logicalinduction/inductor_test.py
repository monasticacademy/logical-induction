from .credence import History
from .formula import Price, Sum, Constant, Product, Max, SafeReciprocal
from .sentence import Atom, Disjunction, Negation
from .inductor import evaluate, find_credences, compute_budget_factor, combine_trading_algorithms, LogicalInductor
from .enumerator import integers


def print_formulas(trading_formulas):
    for sentence, formula in trading_formulas.items():
        print(sentence)
        print(formula.tree())
        print()


def test_evaluate():
    world = {1: True, 2: False, 3: False}
    credence_history = History([
        {1: .6},                        # credences after first update
        {1: .7, 2: .4},                 # credences after second update
        {1: .8, 2: .1, 3: .5, 4: .5},
    ])
    trading_formulas = {
        1: Price(1, 2),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the second update
        2: Price(2, 3),   # purchase tokens for sentence 2 in quantity equal to the credence for sentence 2 after the third update
    }
    value = evaluate(trading_formulas, credence_history, world)
    expected_value = .7 * (1 - .8) + .1 * (0 - .1)
    assert value == expected_value


def test_find_credences_trivial():
    credence_history = History([])  # empty history
    trading_formulas = {
        1: Price(1, 1),   # purchase tokens for sentence 1 in quantity equal to the credence for sentence 1 after the first update
    }
    new_credences = find_credences(trading_formulas, credence_history, 0.5)
    assert new_credences[1] == 0


def test_find_credences_single():
    credence_history = History([])  # empty history
    trading_formulas = {
        # purchase sentence 1 in quantity 1 - 3 * credence
        1: Sum(
            Constant(1),
            Product(
                Constant(-3),
                Price(1, 1))),
    }

    new_credences = find_credences(trading_formulas, credence_history, 1e-5)

    # setting credence to 1/3 yields a trade quantity of zero, which satisfies
    assert abs(new_credences[1] - 1/3) < 1e-8


def test_find_credences_multiple():
    credence_history = History([])  # empty history; we are on the first update
    trading_formulas = {
        # purchase sentence 1 in quantity max(credence-of-sentence-1, credence-of-sentence-2)
        1: Max(
            Price(1, 1),
            Price(2, 1)),
        # purchase sentence 2 in quantity 1 - credence-of-sentence-1 - credence-of-sentence-2
        2: Sum(
            Constant(1),
            Sum(
                Product(
                    Constant(-1),
                    Price(1, 1)),
                Product(
                    Constant(-1),
                    Price(2, 1))))
    }

    new_credences = find_credences(trading_formulas, credence_history, 1e-5)

    # setting credence[1] to 1 and credence[2] to 0 satisfies the conditions
    assert abs(new_credences[1] - 1) < 1e-8
    assert abs(new_credences[2] - 0) < 1e-8


def test_compute_budget_factor_simple():
    phi = Atom("ϕ")

    # we are on the first update; our history is all empty
    past_credences = History([])  # no past credences
    past_trading_formulas = []  # no past trading formulas
    past_observations = []  # no past observations

    # we observed phi in our most recent update
    latest_observation = phi

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert isinstance(budget_factor, SafeReciprocal)
    
    # our world consists of only one base fact (phi), and we observed phi, so
    # the world where phi=true is only one world propositionally consistent with
    # our observations, and in this world we purchase 10 tokens of phi, which
    # could cost anywhere from $0 to $10 depending on the as-yet-unknown
    # credence for phi, and will have a value of exactly $10 in this world. In
    # no case will the value of our holdings drop below -$2, so we expect a
    # budget factor that evaluates to 1 for all credences in [0, 1].
    assert budget_factor.evaluate(past_credences.with_next_update({phi: 0.})) == 1.
    assert budget_factor.evaluate(past_credences.with_next_update({phi: .2})) == 1.
    assert budget_factor.evaluate(past_credences.with_next_update({phi: .6})) == 1.
    assert budget_factor.evaluate(past_credences.with_next_update({phi: 1.})) == 1.


def test_compute_budget_factor_two_base_facts():
    phi = Atom("ϕ")
    psi = Atom("Ψ")

    # we are on the first update; our history is all empty
    past_credences = History([])  # no past credences
    past_trading_formulas = []  # no past trading formulas
    past_observations = []  # no past observations

    # we observe psi in our most recent update
    latest_observation = Disjunction(phi, psi)

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = compute_budget_factor(
        budget,
        past_observations,
        latest_observation,
        past_trading_formulas,
        latest_trading_formulas,
        past_credences)

    assert isinstance(budget_factor, SafeReciprocal)

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
    assert abs(budget_factor.evaluate(past_credences.with_next_update({phi: 1.})) - .2) < 1e-8

    # if the credence for phi were 0.4 then in the third world we would end up with a
    # net worth of -$4, so we should multiply our trading volume by 0.5
    assert abs(budget_factor.evaluate(past_credences.with_next_update({phi: .4})) - .5) < 1e-8

    # if the credence for phi were 0.2 then in the third world we would end up with a
    # net worth of -$2, which is right on budget, so our scaling factor should be 1
    assert abs(budget_factor.evaluate(past_credences.with_next_update({phi: .2})) - 1.) < 1e-8

    # if the credence for phi were 0 then in the third world we would end up with a
    # net worth of $0, which is above budget, so our scaling factor should be 1
    assert abs(budget_factor.evaluate(past_credences.with_next_update({phi: 0.})) - 1.) < 1e-8

def test_compute_budget_factor_already_overran_budget():
    phi = Atom("ϕ")
    psi = Atom("Ψ")

    # there was one previous observation, which was "phi OR psi"
    past_observations = [Disjunction(phi, psi)]

    # on our one previous update, our credences were as follows
    past_credences = History([{
        phi: .6,
        psi: .7,
    }])

    # on the previous update we purchased one token of psi
    past_trading_formulas = [{
        psi: Constant(10),
    }]

    # we observe psi in our most recent update
    latest_observation = Disjunction(phi, psi)

    # our trading formula says to always purchase 10 tokens of phi
    latest_trading_formulas = {
        phi: Constant(10),
    }

    # our budget is $2, which means we can lose up to $2, or, in other words,
    # the value of our holdings is allowed to go as low as -$2
    budget = 2

    # compute the budget factor
    budget_factor = compute_budget_factor(
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
    assert isinstance(budget_factor, Constant)
    assert budget_factor.k == 0


def test_combine_trading_algorithms_simple():
    phi = Atom("ϕ")
    psi = Atom("Ψ")

    # in this test we are on the first update, so there is one trading
    # algorithm, one observation, and no historical credences
    trading_formula = {phi: Constant(1)}
    trading_histories = [[trading_formula]]
    observation_history = [psi]
    credence_history = History([])

    # create the compound trader, which just has one internal trader
    compound_trader = combine_trading_algorithms(
        trading_histories,
        observation_history,
        credence_history,
    )

    assert len(compound_trader) == 1
    assert isinstance(compound_trader[phi], Sum)
    assert len(compound_trader[phi].terms) == 3


def test_logical_inductor_simple():
    phi = Atom("ϕ")
    psi = Atom("Ψ")

    # create a trading algorithm that purchases 1, 2, 3, ... tokens of phi
    def trading_algorithm(sentence, start=1, step=1):
        for quantity in integers(start=start, step=step):
            yield {sentence: Constant(quantity)}

    lia = LogicalInductor()

    credences = lia.update(Negation(phi), trading_algorithm(phi, start=1, step=1))
    print(credences)

    credences = lia.update(psi, trading_algorithm(psi, start=-1, step=-1))
    print(credences)

    credences = lia.update(psi, trading_algorithm(psi, start=-1, step=-1))
    print(credences)
