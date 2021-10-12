import itertools
from collections.abc import Sequence
from typing import Optional
from typing import Union

from . import config
from .note import Note
from .note import SpecificNote


def iterate(
    start_note: Union[str, Note, SpecificNote] = config.chromatic_notes[0],
    take_n: Optional[int] = None,
):
    names = itertools.cycle(config.chromatic_notes)

    if isinstance(start_note, SpecificNote):
        octaves = itertools.chain.from_iterable(
            itertools.repeat(octave, 12)
            for octave in itertools.count(start=start_note.octave)
        )
        notes = (SpecificNote(name, octave) for name, octave in zip(names, octaves))
    else:
        if isinstance(start_note, str):
            start_note = Note(start_note)
        notes = (Note(name) for name in names)

    notes = itertools.dropwhile(lambda note: note.name != start_note.name, notes)

    if take_n is not None:
        notes = itertools.islice(notes, take_n)

    yield from notes


def nth(start_note: Union[str, Note, SpecificNote], n: int):
    return next(itertools.islice(iterate(start_note), n, None))


def sort_notes(it: Sequence[Union[str, Note]]):
    """
    todo: sort Sequence[SpecificNote]
    """
    if isinstance(it[0], str): return sorted(it, key=config.note_i.__getitem__)
    elif type(it[0]) is Note: return sorted(it, key=lambda note: note.i)
    elif type(it[0]) is SpecificNote: return sorted(it, key=lambda note: note.absolute_i)
    else: raise TypeError
