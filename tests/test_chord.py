import random

import pytest

from piano_scales import config
from piano_scales.chord import Chord
from piano_scales.chord import SpecificChord
from piano_scales.note import Note
from piano_scales.note import SpecificNote


def test_creation_from_notes():
    assert str(Chord(frozenset({Note('C'), Note('E'), Note('G')}), root=Note('C'))) == 'CEG/C'


def test_creation_from_str():
    assert str(Chord(frozenset({'C', 'E', 'G'}), root=Note('C'))) == 'CEG/C'


def test_notes():
    assert Chord(frozenset({'C', 'E', 'G'}), root=Note('C')).notes == frozenset({Note('C'), Note('E'), Note('G')})
    assert Chord.from_name('C', 'major').notes == frozenset({Note('C'), Note('E'), Note('G')})


@pytest.mark.xfail(reason='todo: sort chromatically even for abstract notes when chord is in 2 octaves')
def test_str_sort_2_octaves():
    assert str(Chord(frozenset({'B', 'D', 'F'}), root='B')) == 'BDF/B'


def test_name():
    assert Chord(frozenset({'C', 'E', 'G'}), root=Note('C')).name == 'major'
    assert Chord(frozenset({'B', 'D', 'F'}), root=Note('B')).name == 'diminished'


def test_intervals():
    assert Chord(frozenset({'C', 'E', 'G'}), root=Note('C')).intervals == frozenset({4, 7})


def test_from_name():
    assert str(Chord.from_name('C', 'major')) == 'CEG/C'


def test_to_primitives():
    for _ in range(100):
        notes = tuple(
            SpecificNote(abstract, octave=random.randint(0, 9))
            for abstract in
            random.choices(config.chromatic_notes, k=random.randint(1, 9))
        )
        root = random.choice(notes).abstract
        notes = frozenset(notes)
        chord = SpecificChord(notes, root)
        assert chord == SpecificChord.from_primitives(chord.to_primitives())



