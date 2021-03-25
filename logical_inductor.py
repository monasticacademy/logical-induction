import trader


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
    support = sorted(set.union(*(formula.domain() for formula in trading_formulas.values())))

    # brute force search over all rational-valued credences between 0 and 1
    for cs in trader.product(trader.rationals_between(0, 1), len(support)):
        next_credences = {sentence: credence for sentence, credence in zip(support, cs)}
        h = credence_history.with_next_update(next_credences)

        # check all possible worlds (all possible truth values for the support sentences)
        satisfied = True
        for truth_values in trader.product([0, 1], len(support)):
            world = {sentence: truth for sentence, truth in zip(support, truth_values)}
            value_of_holdings = evaluate(trading_formulas, h, world)
            if value_of_holdings > tolerance:
                satisfied = False
                break

        if satisfied:
            return next_credences
