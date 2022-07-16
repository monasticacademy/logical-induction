import collections

from logicalinduction import credence, inductor, formula, sentence, enumerator


def trade_on_probability(sentence, day, p, slope=10):
    return formula.Min(
        formula.Constant(1),
        formula.Max(
            formula.Constant(-1),
            formula.Sum(
                formula.Constant(slope * p),
                formula.Product(
                    formula.Constant(-slope),
                    formula.Price(sentence, day)
                )
            )
        )
    )


def sum_trading_formulae(formulae):
    terms_by_sentence = collections.defaultdict(list)
    for f in formulae:
        for sentence, expr in f.items():
            terms_by_sentence[sentence].append(expr)

    return {
        sentence: formula.Sum(*terms)
        for sentence, terms in terms_by_sentence.items()
    }

def main():
    num_days = 100

    atom = sentence.Atom("atom")

    # create a trading algorithm that trades on all sentences according to a fixed probability
    def trading_algorithm(p):
        for day in enumerator.integers(start=1):
            yield {
                atom: trade_on_probability(atom, day, p)
            }

    # create three trading formulae
    algorithms = [
        trading_algorithm(.1),
        trading_algorithm(.2),
        trading_algorithm(.3)
    ]

    # run a simple unbudgeted 
    history = credence.History()
    for day in range(num_days):
        formulae = [next(alg) for alg in algorithms]
        summed = sum_trading_formulae(formulae)
        tolerance = 2 ** -day
        credences = inductor.find_credences(summed, history, tolerance)
        history = history.with_next_update(credences)

        print("\nday {}:".format(day))
        for s, c in credences.items():
            print("  {:40s} {:f}".format(str(s), float(c)))


if __name__ == "__main__":
    main()
