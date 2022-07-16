
class History(object):
    """Represents a sequence of belief states."""

    def __init__(self, credences=[]):
        self._credences = credences

    def lookup(self, sentence, day):
        assert 1 <= day and day <= len(self._credences), \
            "day index should be in [1, {}] but got {}".format(
                len(self._credences), day)
        return self._credences[day-1].get(sentence, 0.)

    def price(self, sentence):
        """Price gets the current price for the given sentence."""
        return self._credences[-1].get(sentence, 0.)

    def with_next_update(self, next_credences):
        return History(self._credences + [next_credences])

    def last_update(self):
        return self._credences[-1]

    def __len__(self):
        return len(self._credences)