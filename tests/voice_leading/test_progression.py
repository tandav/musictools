import pytest

from musictool.chord import SpecificChord
from musictool.note import SpecificNote
from musictool.noteset import note_range
from musictool.scale import NoteSet
from musictool.scale import Scale
from musictool.voice_leading import progression
from musictool.voice_leading.progression import Progression


@pytest.fixture
def four_chords():
    a = SpecificChord.random()
    b = SpecificChord.random()
    c = SpecificChord.random()
    d = SpecificChord.random()
    return a, b, c, d


@pytest.fixture
def progression4():
    a = SpecificChord.from_str('C1_E1_G1')
    b = SpecificChord.from_str('D1_F1_A1')
    c = SpecificChord.from_str('E1_G1_B1')
    d = SpecificChord.from_str('F1_A1_C2')
    return Progression([a, b, c, d])


def test_validation():
    with pytest.raises(TypeError):
        Progression([0, 1, 2])
    Progression([SpecificChord.random(), SpecificChord.random()])


def test_list_like(four_chords):
    a, b, c, d = four_chords
    p = Progression([a, b, c])
    assert len(p) == 3
    assert p[0] == a
    assert p == [a, b, c]
    e = [a, b, c, d]
    assert p + [d] == e
    p.append(d)
    assert p == e
    assert Progression(x for x in [a, b, c, d]) == [a, b, c, d]


def test_all(progression4):
    def check(x, y): return x[0] < y[0]
    assert progression4.all([check])
    assert progression4.all_not([lambda x, y: not check(x, y)])


def test_distance(progression4):
    assert progression4.distance == 30


def test_transpose_unique_key(four_chords):
    a, b, c, d = four_chords
    d_ = SpecificChord(frozenset((d.notes_ascending[0] + 12,) + d.notes_ascending[1:]))
    p0 = Progression([a, b, c, d])
    p1 = Progression([a, b, c, d_])
    p2 = Progression(SpecificChord(frozenset(n + 12 for n in chord.notes)) for chord in p0)
    p3 = Progression(SpecificChord(frozenset(n + 1 for n in chord.notes)) for chord in p0)
    assert p0.transpose_unique_key != p1.transpose_unique_key
    assert p0.transpose_unique_key == p2.transpose_unique_key
    assert p0.transpose_unique_key != p3.transpose_unique_key


@pytest.mark.parametrize('noteset, note_range_, chord_str, transitions, unique_abstract', (
    (Scale.from_name('C', 'major'), ('A0', 'D2'), 'C1_E1_G1', {'B0_E1_G1', 'C1_D1_G1', 'C1_E1_A1', 'C1_E1_F1', 'C1_F1_G1', 'D1_E1_G1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_E1_G1', {'B0_E1_G1', 'C1_D1_G1', 'C1_E1_A1', 'C1_E1_F1', 'C1_F1_G1', 'D1_E1_G1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_D1_E1', {'B0_D1_E1', 'C1_D1_F1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'B0_C1_D1', {'B0_C1_E1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'F1_G1_A1', {'E1_G1_A1', 'F1_G1_B1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'D1_E1_C2', {'C1_E1_C2', 'D1_E1_B1', 'D1_E1_D2', 'D1_F1_C2'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'D1_E1_C2', {'D1_E1_B1', 'D1_F1_C2'}, True),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_E1', {'B0_E1', 'C1_D1', 'C1_F1', 'D1_E1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_D1', {'B0_D1', 'C1_E1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_D1_E1_F1', {'B0_D1_E1_F1', 'C1_D1_E1_G1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_D1_E1_F1', {'B0_D1_E1_F1', 'C1_D1_E1_G1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_E1_G1_B1', {'B0_E1_G1_B1', 'D1_E1_G1_B1', 'C1_E1_F1_B1', 'C1_E1_A1_B1', 'C1_E1_G1_C2', 'C1_F1_G1_B1', 'C1_D1_G1_B1', 'C1_E1_G1_A1'}, False),
    (NoteSet(frozenset('CDEFGAB')), ('A0', 'D2'), 'C1_E1_G1_B1', {'D1_E1_G1_B1', 'C1_D1_G1_B1', 'C1_E1_F1_B1', 'C1_E1_A1_B1', 'C1_E1_G1_A1', 'C1_F1_G1_B1'}, True),
    (NoteSet(frozenset('CdeFGab')), ('a0', 'd2'), 'C1_e1_G1', {'b0_e1_G1', 'C1_d1_G1', 'C1_e1_a1', 'C1_e1_F1', 'C1_F1_G1', 'd1_e1_G1'}, False),
))
def test_chord_transitons(noteset, note_range_, chord_str, transitions, unique_abstract):
    chord = SpecificChord.from_str(chord_str)
    note_range_ = note_range(SpecificNote.from_str(note_range_[0]), SpecificNote.from_str(note_range_[1]), noteset)
    assert set(map(str, progression.chord_transitons(chord, note_range_, unique_abstract))) == transitions


def test_transition_graph():
    note_range_ = note_range(SpecificNote('A', 0), SpecificNote('D', 2), NoteSet(frozenset('CDEFGAB')))
    graph = progression.transition_graph(SpecificChord.from_str('C1_E1_G1'), note_range_)
    assert len(graph) == 80
    assert sum(map(len, graph.values())) == 300