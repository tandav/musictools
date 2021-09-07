import pytest

from piano_scales.note import Note
from piano_scales.scale import Scale


def test_kind():
    assert Scale('C', 'major').kind == 'diatonic'


def test_equal():
    assert Scale('C', 'major') == Scale('C', 'major')
    assert Scale('C', 'major') == Scale(Note('C'), 'major')
    assert Scale(Note('C'), 'major') == Scale(Note('C'), 'major')
    assert Scale(Note('C'), 'major') != Scale(Note('E'), 'major')


@pytest.mark.parametrize(
    ('scale_name', 'expected_notes'),
    (('major', 'CDEFGAB'), ('phrygian', 'CdeFGab')),
)
def test_notes(scale_name, expected_notes):
    assert ''.join(note.name for note in Scale('C', scale_name).notes) == expected_notes
