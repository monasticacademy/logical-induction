

class History(object):
    """Represents a sequence of belief states."""

    def __init__(self, credences):
        self._credences = credences

    def lookup(self, sentence, update):
        if update > len(self._credences):
            raise AssertionError("price requested for update {} from a history containing only {} updates".format(iter, len(self._credences)))
        return self._credences[update-1].get(sentence, 0.)

    def price(self, sentence):
        """Price gets the current price for the given sentence."""
        return self._credences[-1].get(sentence, 0.)

    def with_next_update(self, next_credences):
        return History(self._credences + [next_credences])

    def __len__(self):
        return len(self._credences)