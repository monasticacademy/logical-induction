import matplotlib
matplotlib.use('Agg')

import seaborn
import matplotlib.figure

import inductor
import sentence
import formula
import enumerator


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


def main():
    # the trading algorithms are constant from the beginning


    # each step we:
    # - learn that the "i-th digit of pi is d" is true/false for a random value of d
    # - add a trading algorithm that trades constant p probability on all observed sentences

    num_days = 1

    # sentences we're going to bet on
    sentences_by_place = []
    for place in range(num_days):
        sentences_by_place.append([
            sentence.Atom("digit {} of pi is {}".format(place+1, d))
            for d in range(10)
        ])

    # flatten the list of sentences
    flat_sentences = []
    for sentences in sentences_by_place:
        flat_sentences.extend(sentences)

    # create a trading algorithm that trades on all sentences according to a fixed probability
    def trading_algorithm(p):
        for day in enumerator.integers(start=1):
            yield {
                sentence: trade_on_probability(sentence, day, p)
                for sentence in flat_sentences
            }

    # set up a search order that fixes all probabilities as equal
    def search_order(sentences):
        for r in enumerator.rationals_between(0, 1):
            yield {sentence: r for sentence in sentences}

    # create the logical inductor
    li = inductor.LogicalInductor()

    # run the logical inductor
    for day in range(num_days):
        foo = .55

        observation = sentences_by_place[day][0]

        trader_probability = .3

        credences = li.update(
            observation,
            trading_algorithm(trader_probability),
            search_order=search_order)

        print("\nafter update {}: p={}".format(day, foo))
        # for s, credence in credences.items():
        #     print("  {:40s} {:f}".format(str(s), float(credence)))

    # # plot the credences over time
    # fig = matplotlib.figure.Figure()
    # ax = fig.add_axes([.1, .1, .8, .8],
    #     xlim=[1, num_days],
    #     ylim=[0, 1],
    #     xlabel="day",
    #     ylabel="credence")
    # ax.plot(range(1, num_days+1), history)
    # fig.savefig("out/history.pdf")

if __name__ == "__main__":
    main()
