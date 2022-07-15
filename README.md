![Continuous integration](https://github.com/alexflint/logical-induction/actions/workflows/integrate.yaml/badge.svg)

# Logical induction in Python

This repository contains code to support the guide to logical induction for
software engineers (which has not yet been published). It consists of a
straightforward python implementation of the logical induction algorithm
published by *Garrabrant et al* in 2018. I have prioritized simplicity over
efficiency.

To run the example code:
```bash
$ git clone git@github.com:alexflint/logical-induction.git
$ cd logical-induction
$ python3 logical_induction_example.py

after update 1:
  the sky is blue                          1.000000
  the sky is blue | the sky is green       0.000000

after update 2:
  the sky is green → the world is round    0.000000
  the sky is blue                          0.000000
  the sky is blue | the sky is green       1.000000
```

### Organization of the code

The main interface is the `LogicalInductor` class in `inductor.py`:

```python
class LogicalInductor(object):
    ...

    def update(self, observation, trading_algorithm):
        """
        Given: 
         * An observation
         * A trading algorithm
        Return:
         * A belief state
        
        Implements the logical induction algorithm as per 5.4.1 in the paper
        """
```

The update function takes as input an observation, which is a logical sentence
that is to be taken to be true from here on, and a trading algorithm, which is a
set of formulas specifying trades to be executed that the logical inductor will
set its credences in order to avoid being exploited by.

The representation of logical sentences is implemented in `sentence.py` and
works as follows. The class `sentence.Atom` represents a claim about the world
not further reducible by logical connectives such as AND, OR, NOT. Its
constructor takes a string, which can be anything and is only to help humans
keep track of what is going on. The other classes in this file implement
conjunctions, disjunctions, logical negation, and material implication.

The representation of trading formulas is implemented in `formula.py`. A trading
formula is a simple language for expressing buy/sell trades that a logical
inductor must not be exploited by. The classes in this file follow section A.2
from the paper.

The representation of belief states and histories of is in `credence.py`. A
belief state is a map from sentences to credences, and a history of belief
states is a list of belief states.

The code in `enumerator.py` provides various routines for enumerating possible
worlds.

The code in `example/two_updates.py` instantiates a logical inductor and
feeds it two observations, printing out the credences it receives in response.
