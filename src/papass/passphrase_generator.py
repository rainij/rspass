import math
from dataclasses import dataclass
from functools import cached_property

from .random.base import RandomNumberGeneratorBase
from .wordlist import WordList


@dataclass
class PassPhraseResult:
    """Represents the result of random phrase generation."""

    phrase: str
    entropy: float
    # Whether we can guarantee that the entropy is that big (otherwise it is just an upper
    # bound which is "probably" not too far off):
    entropy_is_guaranteed: bool


class PassPhraseGenerator:
    """Generate phrases from a wordlist using a random number generator."""

    _wordlist: WordList
    _rng: RandomNumberGeneratorBase

    _delimiter: str

    def __init__(
        self,
        *,
        wordlist: WordList,
        rng: RandomNumberGeneratorBase,
        delimiter: str = " ",
    ):
        """Create a passphrase generator.

        :param wordlist: The words to draw from.
        :param rng: The random source to be used to draw words.
        :param delimiter: At most a single character to be put between the generated words.
        """
        assert len(delimiter) <= 1, "--delimiter must be single character or empty."

        self._wordlist = wordlist
        self._rng = rng
        self._delimiter = delimiter

    def get_phrase(self, count: int) -> PassPhraseResult:
        """Generate a random phrase.

        The phrase is generated by successive applications of ``rng.choice`` to the wordlist.
        """
        return PassPhraseResult(
            phrase=self._delimiter.join([self._choose_word(i + 1) for i in range(count)]),
            entropy=count * self._entropy_per_word,
            entropy_is_guaranteed=self._entropy_is_guaranteed(count),
        )

    def _choose_word(self, _index: int) -> str:
        return self._rng.choice(self._wordlist)

    @property
    def _entropy_per_word(self) -> float:
        return math.log2(len(self._wordlist))

    def _entropy_is_guaranteed(self, count: int) -> bool:
        """Returns True if we can guarantee that the entropy estimate is exact.

        We use a simple heuristic: If the delimiter does not occur in any of the words it
        serves as marker forfor the word boundaries. In that case the number of possible
        passphrases is indeed

        number_of_words_in_wordlist ** number_of_words_in_passphrase

        and the entropy estimate is correct.

        If the heuristic is not satisfied it can in principle still be the case that the
        number of possible passphrases is as desired. But it is hard to check this in
        general so we just return False in that case (we could not prove that it is the
        case).

        But note that in general we entropy is "probably" not too far off.
        """
        assert len(self._delimiter) <= 1

        if count <= 1:
            # In this case delimiter is not even used
            return True
        elif self._delimiter == "":
            return False
        elif self._delimiter in self._word_alphabet:
            return False

        return True

    @cached_property
    def _word_alphabet(self) -> set[str]:
        """Set of letters occuring the words."""
        return set().union(*self._wordlist)