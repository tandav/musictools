import itertools
import pytest

from musictools import voice_leading
from musictools.chord import SpecificChord
from musictools.note import SpecificNote
from musictools.scale import Scale

@pytest.mark.xfail(reason='deprecated')
def test_count_all_triads():
    assert len(voice_leading.all_triads()) == 972


def test_have_parallel_interval():
    # fifths
    a = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('G', 5)}))
    b = SpecificChord(frozenset({SpecificNote('F', 5), SpecificNote('A', 5), SpecificNote('C', 6)}))
    c = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('F', 5), SpecificNote('A', 5)}))
    d = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('B', 5)}))
    h = SpecificChord(frozenset({SpecificNote('D', 5), SpecificNote('F', 5), SpecificNote('A', 5)}))
    i = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('G', 6)}))
    j = SpecificChord(frozenset({SpecificNote('F', 5), SpecificNote('A', 5), SpecificNote('C', 7)}))

    assert voice_leading.have_parallel_interval(a, b, 7)
    assert voice_leading.have_parallel_interval(a, h, 7)
    assert voice_leading.have_parallel_interval(i, j, 7)
    assert not voice_leading.have_parallel_interval(a, c, 7)
    assert not voice_leading.have_parallel_interval(a, d, 7)

    # octaves
    e = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('C', 6)}))
    f = SpecificChord(frozenset({SpecificNote('D', 5), SpecificNote('F', 5), SpecificNote('D', 6)}))
    g = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('E', 6)}))
    assert voice_leading.have_parallel_interval(e, f, 0)
    assert not voice_leading.have_parallel_interval(g, f, 0)


def test_have_hidden_parallel():
    a = SpecificChord(frozenset({SpecificNote('E', 5), SpecificNote('G', 5), SpecificNote('C', 6)}))
    b = SpecificChord(frozenset({SpecificNote('F', 5), SpecificNote('A', 5), SpecificNote('F', 6)}))
    c = SpecificChord(frozenset({SpecificNote('F', 5), SpecificNote('G', 5), SpecificNote('C', 6)}))
    d = SpecificChord(frozenset({SpecificNote('F', 5), SpecificNote('A', 5), SpecificNote('C', 6)}))
    e = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('B', 5)}))
    f = SpecificChord(frozenset({SpecificNote('D', 5), SpecificNote('D', 7)}))
    g = SpecificChord(frozenset({SpecificNote('C', 5), SpecificNote('E', 5), SpecificNote('F', 5)}))
    h = SpecificChord(frozenset({SpecificNote('D', 5), SpecificNote('F', 5), SpecificNote('A', 5)}))
    i = SpecificChord(frozenset({SpecificNote('D', 5), SpecificNote('F', 5), SpecificNote('A', 6)}))
    assert voice_leading.have_hidden_parallel(a, b, 0)
    assert voice_leading.have_hidden_parallel(e, f, 0)
    assert voice_leading.have_hidden_parallel(g, h, 7)
    assert voice_leading.have_hidden_parallel(g, i, 7)
    assert not voice_leading.have_hidden_parallel(c, b, 0)
    assert not voice_leading.have_hidden_parallel(c, d, 0)


def test_have_voice_overlap():
    a = SpecificChord(frozenset({SpecificNote('E', 3), SpecificNote('E', 5), SpecificNote('G', 5), SpecificNote('B', 5)}))
    b = SpecificChord(frozenset({SpecificNote('A', 3), SpecificNote('C', 4), SpecificNote('E', 4), SpecificNote('A', 4)}))
    assert voice_leading.have_voice_overlap(a, b)


@pytest.mark.parametrize(('scale', 'chord_str', 'transitions'), (
    (Scale('C', 'major'), 'C1_E1_G1', {'B0_E1_G1', 'C1_D1_G1', 'C1_E1_A1', 'C1_E1_F1', 'C1_F1_G1', 'D1_E1_G1'}),
    (Scale('C', 'major'), 'C1_D1_E1', {'B0_D1_E1', 'C1_D1_F1'}),
    (Scale('C', 'major'), 'B0_C1_D1', {'B0_C1_E1'}),
    (Scale('C', 'major'), 'F1_G1_A1', {'E1_G1_A1', 'F1_G1_B1'}),
))
def test_chord_transitons(scale, chord_str, transitions):
    chord = SpecificChord.from_str(chord_str)
    octaves = range(3)
    note_range = tuple(SpecificNote(note, octave) for octave, note in itertools.product(octaves, scale.notes))[5:-5]
    assert set(map(str, voice_leading.chord_transitons(chord, note_range))) == transitions
