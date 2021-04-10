import itertools

import enumerator
import trader


def union(sequences):
    """Compute the union of a sequence of sequences."""
    sets = list(set(seq) for seq in sequences)
    if len(sets) == 0:
        return set()
    else:
        return set.union(*(x for x in sets))


def evaluate(trading_formulas, credence_history, world):
    """
    Compute the value of the trades executed by trading_formulas in the given
    world.
    """
    value_of_holdings = 0
    for sentence, formula in trading_formulas.items():
        # compute the quantity of tokens purchased for this sentence 
        quantity = formula.evaluate(credence_history)
        # compute the price paid for those tokens
        price = credence_history.price(sentence)
        # compute the value of these tokens in the given world
        payout = float(world[sentence])
        # add the profit or loss to the net value
        value_of_holdings += quantity * (payout - price)

    return value_of_holdings


def find_credences(trading_formulas, credence_history, tolerance):
    """
    Find a set of credences such that the value-of-holdings for the trades
    executed by trading_formulas are not greater than tolerance in any world.
    """

    # compute the set of sentences upon whose truth value the net holdings of our trader depends
    support = set(trading_formulas.keys())

    # compute the set of sentences over which we should search for credences
    search_domain = union(formula.domain() for formula in trading_formulas.values()).union(support)

    # brute force search over all rational-valued credences between 0 and 1
    for cs in enumerator.product(enumerator.rationals_between(0, 1), len(search_domain)):
        credences = {sentence: credence for sentence, credence in zip(support, cs)}
        h = credence_history.with_next_update(credences)

        # check all possible worlds (all possible truth values for the support sentences)
        satisfied = True
        for truth_values in itertools.product([0, 1], repeat=len(support)):
            world = {sentence: truth for sentence, truth in zip(support, truth_values)}
            value_of_holdings = evaluate(trading_formulas, h, world)
            if value_of_holdings > tolerance:
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
    next_trading_formulas,
    credence_history):
    """
    Returns a trading formula representing a weight that can be multiplied with
    each formula in next_trading_formulas in order to guarantee that the
    trader's value-of-holdings will not fall below the given budget in any
    world.

    The worlds considered are those that are propositionally consistent with the
    sentences in observation_history and next_observation.

    The lists observation_history, trading_history, and credence_history all
    have the same length.

    next_observation is the most recently observed sentence.

    next_trading_formulas is a list of (sentence, formula) pairs that will be
    evaluated on whatever credences the logical inductor outputs when it updates
    its credences in light of next_observation. We do not get to see these
    credences when computing the budget factor because the budget factor is an
    input to the process by which the logical inductor updates its credences.
    """
    assert budget > 0

    history_length = len(observation_history)

    # compute the support for all trading formulas over all days
    support = union(set(trader.keys()) for trader in trading_history)

    # evaluate the "if" clause in (5.2.1)
    for i in range(history_length):
        observations_up_to_i = set(observation_history[:i+1])
        # go over the worlds consistent with the first N observations
        for world in worlds_consistent_with(observations_up_to_i, support):
            # calculate the accumulated value of the trader up to update N
            accumulated_value = 0
            for cur_trading_formulas in trading_history[:i+1]:
                accumulated_value += evaluate(cur_trading_formulas, credence_history, world)
                if accumulated_value < -budget + 1e-7:
                    # we have exceeded our budget on a previous update so we
                    # have no more money to trade now
                    return trader.ConstantFeature(0)

    # create a set of observations up to and including the most recent
    observations = set(observation_history)
    observations.add(next_observation)

    # add atoms for next_trading_formula to the support set
    support.update(set(next_trading_formulas.keys()))

    # if we got this far then we have not already exceeded our budget, so now
    # compute the budget factor
    budget_divisors = []
    for world in worlds_consistent_with(observations, support):
        # compute our accumulated value in this world
        accumulated_value = 0
        for cur_trading_formulas in trading_history:
            accumulated_value += evaluate(cur_trading_formulas, credence_history, world)

        # the money we have left to trade now is our original budget, plus
        # (resp. minus) any money we made (resp. lost) since the beginning of
        # time
        remaining_budget = budget + accumulated_value

        # this value should be positive given the check that we did above
        assert remaining_budget > 1e-8
        remaining_budget_recip = 1. / remaining_budget

        # construct a trading formula representing the value of
        # next_trading_formulas in this world, as a function of the
        # yet-to-be-determined credences for the latest update
        value_of_holdings_terms = []
        for sentence, trading_formula in next_trading_formulas.items():
            # construct a trading formula that looks up the price of tokens for this sentence
            price = trader.PriceFeature(sentence, history_length+1)

            # construct a trading formula that computes the value that this
            # sentence pays out in this world
            payout = trader.ConstantFeature(float(world[sentence]))

            # construct a trading formula that computes the net value of
            # purchasing one token of this sentence, which is the payout from the
            # token minus the price paid to purchase the token
            value = trader.SumFeature(
                payout,
                trader.ProductFeature(
                    trader.ConstantFeature(-1),
                    price))

            # construct a trading formula that multiplies the number of tokens that we
            # purchase by their profitability
            value_of_holdings_terms.append(trader.ProductFeature(
                trading_formula,
                value))

        # construct a trading formula representing the value of the trades
        # executed on this update in this world
        value_of_holdings = trader.SumFeature(*value_of_holdings_terms)

        # construct a trading formula representing the negation of the above
        neg_value_of_holdings = trader.ProductFeature(
            trader.ConstantFeature(-1),
            value_of_holdings)

        # construct a trading formula representing the value we would need to
        # divide our trades by in this world in order to make sure we do not
        # exceed our remaining budget
        divisor_in_this_world = trader.ProductFeature(
            trader.ConstantFeature(remaining_budget_recip),
            neg_value_of_holdings)

        # add the budget factor for this world to the list of terms
        budget_divisors.append(divisor_in_this_world)    

    # the final budget divisor is the max of all the possible budget divisors.
    budget_divisor = trader.MaxFeature(*budget_divisors)

    # now take the safe reciprocal of the divisor, which turns it into a
    # multiplicative factor and also clips it to 1, so that we only scale
    # traders down, not up. This is what we want because if a trader is below
    # its budget then there is no need to scale it up until it uses all of its
    # remaining budget.
    budget_factor = trader.SafeReciprocalFeature(budget_divisor)

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


def trading_firm(credence_history, observation_history, trading_algorithms):
    """
    Given:
     * A sequence of N-1 belief states (credence_history)
     * A sequence of N sentences (observation_history)
     * A sequence of N generators over trading formulas (trading_algorithms)

    Compute a trading formula for day N that incorporates the wisdom from the N
    trading algorithms as a single formula. The returned trading formula
    exploits any market that any of the N constituent trading algorithms
    exploits.

    This function implements TradingFirm as defined in 5.3.2 in the logical
    induction paper.
    """
    n = len(credence_history) + 1
    assert len(observation_history) == n
    assert len(trading_algorithms) == n

    # evaluate the first N traders, zeroing out the first K elements of each
    trading_histories = []
    for k, ta in enumerate(trading_algorithms):
        trading_history = []
        for i, trading_formula in enumerate(itertools.islice(ta, 0, n)):
            if i < k:
                trading_history.append({})
            else:
                trading_history.append(trading_formula)
        
        trading_histories.append(trading_history)

    # compute the terms that should be added together to produce the final
    # trading formula
    terms_by_sentence = collections.defaultdict(list)
    for k, trading_history in enumerate(trading_histories):  # this is the loop over \Sum_{k<=n}
        # compute an upper bound on the net value for this trading history
        net_value_bound = 0
        for trading_formula in trading_history:
            for sentence, trading_expr in trading_formula.items():
                # TODO: where does this 2 come from? (see last para of proof of 5.3.2)
                net_value_bound += 2 * trading_expr.bound()

        net_value_bound = math.ceil(net_value_bound)

        # TODO: we can compute a better bound by using the N-1 belief states
        # that we have already observed in credence_history

        for budget in range(net_value_bound):
            budget_factor = compute_budget_factor(
                budget,
                observation_history[:-1],
                observation_history[-1],
                trading_history[:-1],
                trading_history[-1],
                credence_history)


            for sentence, trading_expr in trading_history[-1].items():
                weight = 2 ** (-k - budget)
                terms_by_sentence[sentence].append(trader.ProductFeature(
                    weight,
                    budget,
                    trading_expr))

        for sentence, trading_expr in trading_history[-1].items():
            weight = 2 ** (-k - net_value_bound)
            terms_by_sentence[sentence].append(trader.ProductFeature(
                weight,
                trading_expr))

    final_trading_formula = {}
    for sentence, terms in terms_by_sentence.items():
        final_trading_formula[sentence] = trader.SumFeature(*terms)

    return final_trading_formula

    

