from collections.abc import Callable, Iterable, Iterator
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from papass.random.dice import DiceRng, compute_dice_frame
from papass.utils import rolls_to_value


def make_patched_input(rolls: Iterable[Iterable[int]]) -> Callable[[Any], str]:
    """Make a patched version of the builtin `input`."""

    def make_iterator() -> Iterator[str]:
        for r in rolls:
            yield " ".join(map(str, r))

        raise AssertionError("Unexpectedly many requests to roll.")

    iterator = make_iterator()
    return lambda _: next(iterator)


def patch_input(monkeypatch, rolls: Iterable[Iterable[int]]):
    patched_input = make_patched_input(rolls)
    monkeypatch.setattr("builtins.input", patched_input)


@pytest.mark.parametrize(
    "num_sides,upper,rolls",
    [
        # `upper` is a power of `num_sides`:
        (
            6,
            6**2,
            [[1, 1]],
        ),
        (
            6,
            6,
            [[4]],
        ),
        (
            6,
            6**3,
            [[6, 6, 6]],
        ),
        (
            8,
            8**6,
            [[1, 2, 3, 4, 5, 6]],
        ),
        (
            20,
            20**3,
            [[17, 3, 13]],
        ),
        # `upper` no power of `num_sides`:
        (
            6,
            6**2 - 5,
            [[6, 6, 6, 6, 6], [2, 3, 2, 3, 1]],
        ),
    ],
)
def test_randbelow(monkeypatch, num_sides, upper, rolls):
    patch_input(monkeypatch, rolls)

    # Only the last roll should be used (others are rejected).
    expected = rolls_to_value(num_sides, rolls[-1]) % upper

    rng = DiceRng(num_sides=num_sides, required_success_probability=0.99)
    assert rng.randbelow(upper) == expected


@given(
    num_sides=st.integers(2, 20),
    upper=st.integers(2, 1000_000),
    req_prob_exponent=st.integers(1, 6),
)
def test_compute_frame(num_sides, upper, req_prob_exponent):
    required_success_probability = 1.0 - 10 ** (-req_prob_exponent)
    # Due to possible floating point issues (not sure if really needed)
    epsilon = 10 ** (-2 * req_prob_exponent)

    result = compute_dice_frame(
        num_sides=num_sides,
        upper=upper,
        required_success_probability=required_success_probability,
    )

    # The success probability is as high as desired
    upper_dice = num_sides**result.required_num_rolls
    upper_multiple = (upper_dice // upper) * upper
    assert upper_multiple == result.upper_multiple
    success_probability = upper_multiple / upper_dice
    assert success_probability > required_success_probability - epsilon

    # Less rolls would not work:
    upper_dice_less = num_sides ** (result.required_num_rolls - 1)
    upper_multiple_less = (upper_dice_less // upper) * upper
    success_probability_less = upper_multiple_less / upper_dice_less
    assert success_probability_less < required_success_probability + epsilon
