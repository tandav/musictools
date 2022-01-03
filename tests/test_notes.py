import pytest

from musictools.notes import bits_to_intervals
from musictools.notes import intervals_to_bits


@pytest.mark.parametrize(('bits', 'intervals'), (
    ('101011010101', frozenset({0, 2, 4, 5, 7, 9, 11})),
    ('110101101010', frozenset({0, 1, 3, 5, 6, 8, 10})),
    ('101001010100', frozenset({0, 2, 5, 7, 9})),
    ('101101010010', frozenset({0, 2, 3, 5, 7, 10})),
))
def test_bits_intervals(bits, intervals):
    assert bits_to_intervals(bits) == intervals
    assert intervals_to_bits(intervals) == bits

