import asyncio
import itertools
import random
from numbers import Number
from typing import Optional
from typing import Union

from . import chromatic
from . import config
from .note import Note
from .note import SpecificNote

intervals_to_name = {
    frozenset({4, 7}): 'major',
    frozenset({3, 7}): 'minor',
    frozenset({3, 6}): 'diminished',
}
name_to_intervals = {v: k for k, v in intervals_to_name.items()}


class Chord:
    def __init__(
        self,
        notes: frozenset[Union[str, Note]],
        root: Optional[Union[str, Note]] = None,
    ):
        """
        chord is an unordered set of notes
        root:
            root note of a chord (to distinguish between inversions_
            root note is optional, some chord can has no root
            chord w/o root has no intervals
        """

        if isinstance(next(iter(notes)), str):
            notes = frozenset(Note(note) for note in notes)

        if isinstance(root, str):
            root = Note(root)

        self.notes = notes
        self.root = root
        self.key = self.notes, self.root

        self.str_chord = ''.join(note.name for note in chromatic.sort_notes(list(self.notes)))

        if root is not None:
            if root not in notes:
                raise ValueError('root note should be one of the chord notes')

            self.intervals = frozenset(note - root for note in notes - {root})
            self.name = intervals_to_name.get(self.intervals)

        # self.str_chord = ''.join(note.name for note in self.notes)
        # self.intervals = tuple(n - self.specific_notes[0] for n in self.specific_notes[1:])
        # self.name = {(3, 7): 'minor', (4, 7): 'major', (3, 6): 'diminished'}.get(self.intervals)
        # self.root = str_chord[0]
        # self.root_octave = root_octave
        # self.notes = tuple(Note(note, root_octave) for note in self.str_chord)
        # self.add_notes_no_inverse()

    @property
    def rootless(self): return Chord(self.notes)

    @classmethod
    def from_name(cls, root: Union[str, Note], name: str):
        if isinstance(root, str):
            root = Note(root)
        intervals = name_to_intervals[name]
        notes = set(chromatic.nth(root, interval) for interval in intervals)
        notes.add(root)
        return cls(frozenset(notes), root)

    @classmethod
    def from_intervals(cls, root: Union[str, Note], intervals: frozenset):

        """
        if you're creating chord from interval, you must specify root note
        from which intervals are calculated
        """
        # instance = cls()
        # instance.intervals
        # instanse.name = {(3, 7): 'minor', (4, 7): 'major', (3, 6): 'diminished'}.get(self.intervals)
        # # name: Optional[str] = None,

        raise NotImplementedError

    def inversions(self):
        raise NotImplementedError

    def __eq__(self, other): return self.key == other.key
    def __hash__(self): return hash(self.key)
    def __len__(self): return len(self.notes)
    def __contains__(self, item): return item in self.notes
    # def __str__(self): return ''.join(note.name for note in self.notes)

    # def to_piano_image(self, base64=False):
    #     return Piano(chord=self)._repr_svg_()

    def __repr__(self):
        # _ = '{' + ' '.join(f'{note.name}' for note in self.notes) + '}'
        # return f"Chord({self.str_chord} / {self.root.name if self.root is not None else self.root})"
        _ = self.str_chord
        if self.root is not None:
            _ += f'/{self.root.name}'
        return _

    async def play(self, seconds=1):
        await SpecificChord(
            notes=frozenset(SpecificNote(note) for note in self.notes),
            root=self.root,
        ).play(seconds)
    #     notes_to_play = self.specific_notes
    #
    #     if bass:
    #         notes_to_play = itertools.chain(notes_to_play, [Note(self.root.name, octave=self.root.octave + bass)])
    #
    #     tasks = tuple(note.play(seconds) for note in notes_to_play)
    #     await asyncio.gather(*tasks)

    # def _repr_html_(self):
    #     label = hasattr(self, 'label') and f"id={self.label!r}"or ''
    #     number = hasattr(self, 'number') and self.number or ''
    #
    #     return f'''
    #     <li class='card {self.name}' {label}>
    #     <a href='play_chord_{self.str_chord}'>
    #     <span class='card_header' ><h3>{number} {self.root} {self.name}</h3></span>
    #     <img src='{self.to_piano_image(base64=True)}' />
    #     </a>
    #     </li>
    #     '''

    # def __repr__(self):
    #     label = hasattr(self, 'label') and f"id={self.label!r}"or ''
    #     number = hasattr(self, 'number') and self.number or ''
    #
    #     return f'''
    #     <li class='card {self.name}' {label} onclick=play_chord('{str(self)}')>
    #     <span class='card_header' ><h3>{number} {self.root} {self.name}</h3></span>
    #     <img src='{self.to_piano_image(base64=True)}' />
    #     </li>
    #     '''


class SpecificChord:
    def __init__(
        self,
        notes: frozenset[SpecificNote],
        root: Optional[Note] = None,
    ):
        self.notes = notes
        self.root = root
        self.abstract = Chord(frozenset(note.abstract for note in notes), root)
        # self.root_specific = frozenset(note for note in notes if note.abstract == root)

        self.notes_ascending = sorted(notes, key=lambda note: note.absolute_i)
        self.intervals = tuple(note - self.notes_ascending[0] for note in self.notes_ascending[1:])  # from lowest note
        self.key = self.notes, self.root
        self.str_chord = '_'.join(repr(note) for note in self.notes_ascending)

    @classmethod
    def random(cls, n_notes=None, octaves=None):
        if n_notes is None:
            n_notes = random.randint(2, 5)
        if octaves is None:
            octaves = 3, 4, 5
        notes_space = tuple(
            SpecificNote(note, octave)
            for note, octave in itertools.product(config.chromatic_notes, octaves)
        )
        notes = frozenset(random.sample(notes_space, n_notes))
        return cls(notes)

    def notes_combinations(self, ids=False):
        if ids: yield from itertools.combinations(range(len(self.notes_ascending)), 2)
        else: yield from itertools.combinations(self.notes_ascending, 2)
        # for n, m in itertools.combinations(self.notes_ascending, 2):
        #     yield n, m

    def find_intervals(self, interval: int):
        return tuple((n, m) for n, m in self.notes_combinations() if abs(m - n) == interval)

    def __repr__(self):
        _ = self.str_chord
        if self.root is not None:
            _ += f'__{self.root.name}'
        return _
        # return ' '.join(note.short_repr() for note in self.notes)

    def __eq__(self, other): return self.key == other.key
    def __hash__(self): return hash(self.key)

    # def __sub__(self, other):
    #     """
    #     https://music.stackexchange.com/a/77630
    #     considering no voice crossing
    #     """
    #     return sum(note.absolute_i for note in self.notes) - sum(note.absolute_i for note in other.notes)

    def __sub__(left, right):
        return sum(abs(l.absolute_i - r.absolute_i) for l, r in zip(left.notes_ascending, right.notes_ascending))

    async def play(self, seconds: Number = 1):
        tasks = [note.play(seconds) for note in self.notes]
        await asyncio.gather(*tasks)