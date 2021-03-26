import enumerate


def union(sequences):
    """Compute the union of a sequence of sequences."""
    return set.union(*(set(seq) for seq in sequences))


def evaluate(trading_formulas, credence_history, world):
    """Compute the value of the trades executed by trading_formulas in the given
    world."""
    value_of_holdings = 0
    for sentence, formula in trading_formulas.items():
        # compute the quantity of tokens purchased for this sentence 
        quantity = formula.evaluate(credence_history)
        # compute the price paid for those tokens
        price = credence_history.price(sentence)
        # compute the value of these tokens in the given world
        value = float(world[sentence])
        # add the profit or loss to the net value
        value_of_holdings += quantity * (value - price)

    return value_of_holdings


def find_credences(trading_formulas, credence_history, tolerance):
    """Find a set of credences such that the value-of-holdings for the trades executed by
    trading_formulas are not greater than tolerance in any world."""

    # compute the set of sentences over which we should search
    support = sorted(union(formula.domain() for formula in trading_formulas.values()))

    # brute force search over all rational-valued credences between 0 and 1
    for cs in enumerate.product(enumerate.rationals_between(0, 1), len(support)):
        next_credences = {sentence: credence for sentence, credence in zip(support, cs)}
        h = credence_history.with_next_update(next_credences)

        # check all possible worlds (all possible truth values for the support sentences)
        satisfied = True
        for truth_values in enumerate.product([0, 1], len(support)):
            world = {sentence: truth for sentence, truth in zip(support, truth_values)}
            value_of_holdings = evaluate(trading_formulas, h, world)
            if value_of_holdings > tolerance:
                satisfied = False
                break

        if satisfied:
            return next_credences


def worlds_consistent_with(domain, observations):
    """
    Enumerate worlds propositionally consistent with the set of observations.

    The set of worlds considered is the set of possible assignments of truth values to the sentence in domain. 

    Each observation is a sentence in propositional logic, with atoms s1, ..., sn

    domain is a list of sentences
    observations is a list of sentences
    """
    # just go over each possible world,
    # evaluate each sentence on each world
    # yield the worlds that are consistent
    domain_atoms = sorted(union(sentence.atoms() for sentence in domain))
    observation_atoms = sorted(union(sentence.atoms() for sentence in observations))
    for truth_values in itertools.product((True, False), repeat=len(atoms)):
        world = {atom: value for atom, value in zip(atoms, truth_values)}
        if all(sentence.evaluate(world) for sentence in observations):
            yield {sentence: sentence.evaluate(world) for sentence in domain}


def budget_trader(budget, observation_history, trading_history, credence_history):
    """Returns a weight for the most recent trading formula in
    trading_history such the value of the trader's holdings will not
    fall below the given budget in any world propositionally consistent with the
    observed sentences.

    trading_history has one more entry than credence_history does
    
    observation_history has the same number of entries as trading_history."""
    n = len(observation_history)

    # compute the support for all trading formulas over all days
    # support = union(formula.domain() for formula in trader for trader in trading_history)

    # for each day 1...n-1:
        # Dm = union(observation_history[1:n-1])
        # accumulated_value = 0
        # for each world propositionally consistent with Dm:  (worlds are over support computed above)
            # evaluate this trader on this world with credences up to current day
            # add value-of-holdings from this day to accumulated_value, which is the accumulatation over all days
            # if accumulated_value is above budget then return 0
    
    # Dn = union(observation_history)
    # terms = []
    # for each world propositionally consistent with Dn:  (worlds are over support computed above)
        # compute prior-earnings = accumualted value for this trader in this world for days 1..n-1
        # compute present-earnings for this trader in this world for day n AS A FUNCTION OF CREDENCES
        # construct max(1, -present-earnings / (budget + prior_earnings)) AS A TRADING FORMULA
        # add this trading formula to the list of terms
    # weight = join the terms together as -max(-term for term in terms)
    # return Product(formula, weight) for formula in present_formulas
