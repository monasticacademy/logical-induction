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

        print("sentence {}: quantity={}, price={}, value={}, net={}".format(sentence, quantity, price, value, quantity*(value-price)))

    return value_of_holdings
