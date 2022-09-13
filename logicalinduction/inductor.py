import itertools
import collections
import math

from . import enumerator
from . import formula
from . import credence


def union(sequences):
    """Compute the union of a sequence of sequences."""
    sets = list(set(seq) for seq in sequences)
    if len(sets) == 0:
        return set()
    else:
        return set.union(*(x for x in sets))


def evaluate(trading_policy, credence_history, world) -> float:
    """
    Compute the value of the trades executed by trading_policy in the given
    world.
    """
    value_of_holdings = 0
    for sentence, formula in trading_policy.items():
        # compute the quantity of tokens purchased for this sentence 
        quantity = formula.evaluate(credence_history)
        # compute the price paid for those tokens
        price = credence_history.price(sentence)
        # compute the value of these tokens in the given world
        payout = float(world[sentence])
        # add the profit or loss to the net value
        value_of_holdings += quantity * (payout - price)

    return value_of_holdings


def rational_credences(sentences):
    """
    Enumerates all rational-valued credences over a set of sentences
    """
    for cs in enumerator.product(enumerator.rationals_between(0, 1), len(sentences)):
        yield {sentence: credence for sentence, credence in zip(sentences, cs)}


def find_credences(trading_policy, credence_history, tolerance, credence_search_order=None):
    """
    Find a set of credences such that the value-of-holdings for the trades
    executed by trading_policy are not greater than tolerance in any world.
    """

    # if no search order specified then brute force all rational-valued credences
    if credence_search_order is None:
        credence_search_order = rational_credences

    # compute the set of sentences upon whose truth value the net holdings of our trader depends
    support = set(trading_policy.keys())

    # compute the set of sentences over which we should search for credences
    search_domain = union(formula.domain() for formula in trading_policy.values()).union(support)

    # brute force search over all rational-valued credences between 0 and 1
    for credences in credence_search_order(search_domain):          # link: search_over_credences
        history = credence_history.with_next_update(credences)

        # check all possible worlds (all possible truth values for the support sentences)
        satisfied = True
        for truth_values in itertools.product([0, 1], repeat=len(support)):     # link: max_over_worlds
            world = {sentence: truth for sentence, truth in zip(support, truth_values)}
            value_of_holdings = evaluate(trading_policy, history, world)

            # there might not be any way to prevent our traders from losing money,
            # so there is no abs() in the below
            if value_of_holdings > tolerance:                         # link: tolerance_check
                satisfied = False
                break

        if satisfied:
            return credences


def worlds_consistent_with(observations, domain):
    """
    Enumerate worlds propositionally consistent with a set of observations.

    The set of worlds considered is the set of possible assignments of truth
    values to the sentence in domain. 

    Each observation is a sentence in propositional logic, with atoms s1, ...,
    sn

    domain is a list of sentences
    
    observations is a list of sentences
    """
    domain_atoms = union(sentence.atoms() for sentence in domain)
    observation_atoms = union(sentence.atoms() for sentence in observations)
    atoms = sorted(set.union(domain_atoms, observation_atoms))
    for truth_values in itertools.product((True, False), repeat=len(atoms)):
        base_facts = {atom: value for atom, value in zip(atoms, truth_values)}
        if all(sentence.evaluate(base_facts) for sentence in observations):
            yield {sentence: sentence.evaluate(base_facts) for sentence in domain}


def compute_budget_factor(
    budget,
    observation_history,
    next_observation,
    trading_history,
    next_trading_policy,
    credence_history):
    """
    Returns a trading formula representing a weight that can be multiplied with
    each formula in next_trading_policy in order to guarantee that the
    trader's value-of-holdings will not fall below the given budget in any
    world.

    The worlds considered are those that are propositionally consistent with the
    sentences in observation_history and next_observation.

    The lists observation_history, trading_history, and credence_history all
    have the same length.

    next_observation is the most recently observed sentence.

    next_trading_policy is a list of (sentence, formula) pairs that will be
    evaluated on whatever credences the logical inductor outputs when it updates
    its credences in light of next_observation. We do not get to see these
    credences when computing the budget factor because the budget factor is an
    input to the process by which the logical inductor updates its credences.
    """
    assert budget > 0

    history_length = len(observation_history)

    # compute the support for all trading formulas over all days
    support = union(set(trading_policy.keys()) for trading_policy in trading_history)

    # evaluate the "if" clause in (5.2.1)
    for i in range(history_length):
        observations_up_to_i = set(observation_history[:i+1])

        # go over the worlds consistent with the first N observations
        for world in worlds_consistent_with(observations_up_to_i, support):

            # calculate the accumulated value of the trader up to update N
            accumulated_value = 0
            for cur_trading_policy in trading_history[:i+1]:
                accumulated_value += evaluate(cur_trading_policy, credence_history, world)

                # if we have exceeded our budget on a previous update then we
                # have no more money to trade now
                if accumulated_value < -budget + 1e-7:
                    return formula.Constant(0)

    # create a set of observations up to and including the most recent
    observations = set(observation_history)
    observations.add(next_observation)

    # add atoms for next_trading_formula to the support set
    support.update(set(next_trading_policy.keys()))

    # if we got this far then we have not already exceeded our budget, so now
    # compute the budget factor
    budget_divisors = []
    for world in worlds_consistent_with(observations, support):     # link: loop_over_consistent_worlds
        # compute our accumulated value in this world
        accumulated_value = 0
        for cur_trading_policy in trading_history:
            accumulated_value += evaluate(cur_trading_policy, credence_history, world)

        # the money we have left to trade now is our original budget, plus
        # (resp. minus) any money we made (resp. lost) since the beginning of
        # time
        remaining_budget = budget + accumulated_value

        # this value should be positive given the check that we did above
        assert remaining_budget > 1e-8
        remaining_budget_recip = 1. / remaining_budget

        # construct a trading formula representing the value of
        # next_trading_policy in this world, as a function of the
        # yet-to-be-determined credences for the latest update
        value_of_holdings_terms = []
        for sentence, trading_formula in next_trading_policy.items():
            # construct a trading formula that looks up the price of tokens for this sentence
            price = formula.Price(sentence, history_length+1)

            # construct a trading formula that computes the value that this
            # sentence pays out in this world
            payout = formula.Constant(float(world[sentence]))

            # construct a trading formula that computes the net value of
            # purchasing one token of this sentence, which is the payout from the
            # token minus the price paid to purchase the token
            value = formula.Sum(
                payout,
                formula.Product(
                    formula.Constant(-1),
                    price))

            # construct a trading formula that multiplies the number of tokens that we
            # purchase by their profitability
            value_of_holdings_terms.append(formula.Product(
                trading_formula,
                value))

        # construct a trading formula representing the value of the trades
        # executed on this update in this world
        value_of_holdings = formula.Sum(*value_of_holdings_terms)

        # construct a trading formula representing the negation of the above
        neg_value_of_holdings = formula.Product(
            formula.Constant(-1),
            value_of_holdings)

        # construct a trading formula representing the value we would need to
        # divide our trades by in this world in order to make sure we do not
        # exceed our remaining budget
        divisor_in_this_world = formula.Product(
            formula.Constant(remaining_budget_recip),
            neg_value_of_holdings)

        # add the budget factor for this world to the list of terms
        budget_divisors.append(divisor_in_this_world)

    # the final budget divisor is the max of all the possible budget divisors.
    budget_divisor = formula.Max(*budget_divisors)

    # now take the safe reciprocal of the divisor, which turns it into a
    # multiplicative factor and also clips it to 1, so that we only scale
    # traders down, not up. This is what we want because if a trader is below
    # its budget then there is no need to scale it up until it uses all of its
    # remaining budget.
    budget_factor = formula.SafeReciprocal(budget_divisor)

    # and we are done!
    return budget_factor

    # in the paper, the computation above is written in (5.2.1) and in the proof
    # of part 1 of (5.2.2) as 
    #
    #    infinum[1 / max(1, divisor)]
    #
    # where "infinum" is like "min" over an infinite set. But this is
    # unnecessarily cumbersome and can be rewritten
    #
    #   1 / max(1, supremum(divisors))
    #
    # where supremum is like "max" over an infinite set. This is easier for us
    # to represent in Trading Language since we have native support for max but
    # not for min.


def combine_trading_algorithms(trading_histories, observation_history, credence_history):
    """
    Given:
     * A sequence of N sequences of trading policies (trading_histories)
     * A sequence of N sentences (observation_history)
     * A sequence of N-1 belief states (credence_history)
    Returns:
     * A single trading formula for day N that incorporates the wisdom from 
       the N trading algorithms. The returned trading formula exploits any
       market that any of the N constituent trading algorithms exploits.

    This function implements TradingFirm as defined in 5.3.2 in the logical
    induction paper.
    """
    n = len(credence_history) + 1
    assert len(observation_history) == n
    assert len(trading_histories) == n

    # compute the terms that should be added together to produce the final
    # trading formula
    terms_by_sentence = collections.defaultdict(list)
    for k, trading_history in enumerate(trading_histories):  # link: loop_over_rows
        # zero out the first k entries
        clipped_trading_history = []
        for i, trading_policy in enumerate(trading_history):
            if i < k:
                clipped_trading_history.append({})
            else:
                clipped_trading_history.append(trading_policy)

        # compute an upper bound on the net value for this trading history
        net_value_bound = 0
        for trading_policy in clipped_trading_history:
            for sentence, trading_expr in trading_policy.items():
                # compute an upper bound on the absolute value of trading_expr,
                # which is the quantity that we will purchase of this sentence
                quantity_bound = trading_expr.bound()

                # Let C = quantity_bound. We might spend up to $C purchasing
                # these tokens, and they might later be worth up to $C, so their
                # net value could be between -$C and $2C. We technically only
                # need a lower bound for the sum below but here we follow the
                # paper and compute a formal bound on the net value of this
                # trade by including the constant 2 below. See the last
                # paragraph of proof of 5.3.2 in the paper.
                net_value_bound += 2 * quantity_bound

        net_value_bound = math.ceil(net_value_bound)

        # TODO: we can compute a better bound by using the N-1 belief states
        # that we have already observed in credence_history

        for budget in range(1, net_value_bound+1):          # link: loop_over_columns
            budget_factor = compute_budget_factor(
                budget,
                observation_history[:-1],
                observation_history[-1],
                clipped_trading_history[:-1],
                clipped_trading_history[-1],
                credence_history)

            for sentence, trading_expr in clipped_trading_history[-1].items():
                weight = 2 ** (-k-1 - budget)
                terms_by_sentence[sentence].append(formula.Product(         # link: apply_budget_transform
                    formula.Constant(weight),
                    budget_factor,
                    trading_expr))

        for sentence, trading_expr in clipped_trading_history[-1].items():
            weight = 2 ** (-k-1 - net_value_bound)
            terms_by_sentence[sentence].append(formula.Product(
                formula.Constant(weight),
                trading_expr))

    # create a trading policy by summing over the terms above
    return {
        sentence: formula.Sum(*terms)
        for sentence, terms in terms_by_sentence.items()
    }


class LogicalInductor(object):
    def __init__(self):
        self._trading_algorithms = []
        self._trading_histories = []
        self._observation_history = []
        self._credence_history = credence.History()

    def update(self, observation, trading_algorithm, search_order=None):
        """
        Given: 
         * An observation
         * A trading algorithm
        Return:
         * A belief state
        
        Implements the logical induction algorithm as per 5.4.1 in the paper
        """

        # add the observation to the list of historical observations
        self._observation_history.append(observation)

        # evaluate one more trading formula for each existing trading algorithm
        for algorithm, history in zip(self._trading_algorithms, self._trading_histories):
            history.append(next(algorithm))

        # evaluate the first N trading formulas for the new trading algorithm
        trading_history = list(itertools.islice(trading_algorithm, len(self._observation_history)))

        # add the new trading algorithm and its history to the list
        self._trading_algorithms.append(trading_algorithm)
        self._trading_histories.append(trading_history)

        # assemble the ensemble trader
        ensemble_policy = combine_trading_algorithms(       # link: the_ensemble_policy
            self._trading_histories,
            self._observation_history,
            self._credence_history)

        # tolerances get tighter as we process more updates
        tolerance = 2 ** -len(self._observation_history)    # link: tolerance_schedule

        # find a set of credences not exploited by the compound trader
        credences = find_credences(                         # link: find_the_credences
            ensemble_policy,
            self._credence_history,
            tolerance,
            search_order)

        # add these credences to the history
        self._credence_history = self._credence_history.with_next_update(credences)

        # return the credences
        return credences
