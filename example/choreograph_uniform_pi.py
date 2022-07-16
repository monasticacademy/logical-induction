import matplotlib
matplotlib.use('Agg')

import seaborn
import matplotlib.figure

from logicalinduction import inductor, formula, sentence, enumerator

def make_s_curve(f, intercept, slope):
    return formula.Min(
        formula.Constant(1),
        formula.Max(
            formula.Constant(-1),
            formula.Sum(
                formula.Constant(slope * intercept),
                formula.Product(
                    formula.Constant(-slope),
                    f
                )
            )
        )
    )


def main():
    # the sentence we're going to bet on
    digit_n_is_k = sentence.Atom("n-th digit of pi is k")

    # create a nonsense atom
    irrelevant = sentence.Atom("foo")

    # create a trading algorithm that bets according to a fixed probability
    def trading_algorithm():
        for day in enumerator.integers(start=1):
            yield {
                digit_n_is_k: make_s_curve(formula.Price(digit_n_is_k, day), .1, 10)
            }

    # create the logical inductor
    li = inductor.LogicalInductor()

    # number of days to run trading for
    num_days = 15

    # run the logical inductor
    history = []
    for day in range(1, num_days+1):
        credences = li.update(irrelevant, trading_algorithm())
        history.append(credences[digit_n_is_k])
        print("\nafter update {}:".format(day))
        for s, credence in credences.items():
            print("  {:40s} {:f}".format(str(s), float(credence)))

    # plot the credences over time
    fig = matplotlib.figure.Figure()
    ax = fig.add_axes([.1, .1, .8, .8],
        xlim=[1, num_days],
        ylim=[0, 1],
        xlabel="day",
        ylabel="credence")
    ax.plot(range(1, num_days+1), history)
    fig.savefig("out/history.pdf")

if __name__ == "__main__":
    main()
