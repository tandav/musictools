from __future__ import annotations

from xml.etree import ElementTree

from musictool.config import BLACK_PALE
from musictool.config import WHITE_PALE
from musictool.config import WHITE_BRIGHT
from musictool.config import BLACK_BRIGHT
from musictool.note import BLACK_NOTES
from musictool.note import WHITE_NOTES
from musictool.note import Note
from musictool.note import SpecificNote
from musictool.noterange import CHROMATIC_NOTESET
from musictool.noterange import NoteRange
from musictool.util.color import css_hex


def note_color(note: Note | SpecificNote) -> int:
    def _note_color(note: Note) -> int:
        return WHITE_PALE if note in WHITE_NOTES else BLACK_PALE
    if isinstance(note, SpecificNote):
        return _note_color(note.abstract)
    elif isinstance(note, Note):
        return _note_color(note)
    else:
        raise TypeError


class Piano:
    def __init__(
        self,
        note_colors: dict[Note | SpecificNote, int] | None = None,
        top_rect_colors: dict[Note | SpecificNote, int] | None = None,
        squares: dict[Note, dict[str, str | int]] | None = None,
        top_rect_height: int = 5,
        square_size: int = 12,
        ww: int = 18,  # white key width
        wh: int = 85,  # white key height
        noterange: NoteRange | None = None,
        black_between: bool = False,
    ):
        self.ww = ww
        self.wh = wh
        self.bw = int(ww * 0.6)
        self.bh = int(wh * 0.6)

        self.top_rect_height = top_rect_height
        self.square_size = square_size

        self.note_colors = note_colors or {}
        self.top_rect_colors = top_rect_colors or {}
        self.squares = squares or {}

        if noterange is not None:
            if noterange.noteset is not CHROMATIC_NOTESET:
                raise ValueError  # maybe this is not necessary

            # ensure that start and stop are white keys
            self.noterange = NoteRange(
                start=noterange.start + -1 if noterange.start.abstract in BLACK_NOTES else noterange.start,
                stop=noterange.stop + 1 if noterange.stop.abstract in BLACK_NOTES else noterange.stop,
            )
        else:
            # render 2 octaves by default
            self.noterange = NoteRange(SpecificNote('C', 0), SpecificNote('B', 1))

        self.white_notes = tuple(note for note in self.noterange if note.abstract in WHITE_NOTES)
        self.black_notes = tuple(note for note in self.noterange if note.abstract in BLACK_NOTES)
        self.size = ww * len(self.white_notes), wh
        self.rects = []

        for note in self.white_notes + self.black_notes:
            x, w, h, c, sx, sy = self.coord_helper(note)

            # draw key
            self.rects.append(f"""<rect class='note' note='{note}' x='{x}' y='0' width='{w}' height='{h}' style='fill:{css_hex(c)};stroke-width:1;stroke:{css_hex(BLACK_PALE)}' onclick="play_note('{note}')"/>""")

            # draw rectangle on top of note
            if rect_color := self.top_rect_colors.get(note, self.top_rect_colors.get(note.abstract)):
                self.rects.append(f"""<rect class='top_rect' note='{note}' x='{x}' y='0' width='{w}' height='{top_rect_height}' style='fill:{css_hex(rect_color)};'/>""")

            # draw squares on notes
            # if fill_border_color := self.squares.get(note, self.squares.get(note.abstract)):
            if payload := self.squares.get(note, self.squares.get(note.abstract)):
                fill_color = css_hex(payload.get('fill_color', WHITE_BRIGHT))
                border_color = css_hex(payload.get('border_color', BLACK_BRIGHT))

                if onclick := payload.get('onclick'):
                    onclick = f" onclick='{onclick}'"
                # <g onclick="play_chord('{str_chord}')">
                # fill, border, text_color, str_chord = fill_border_color
                # note.name

                rect = f"<rect class='square' note='{note}' x='{sx}' y='{sy}' width='{square_size}' height='{square_size}' style='fill:{fill_color};stroke-width:1;stroke:{border_color}'/>"

                if text := payload.get('text'):
                    text_color = css_hex(payload.get('text_color', BLACK_BRIGHT))
                    rect += f"<text class='square' note='{note}' x='{sx}' y='{sy + square_size}' font-family=\"Menlo\" font-size='15' style='fill:{text_color}'>{text}</text>"

                self.rects.append(f"""
                    <g{onclick}>
                        {rect}                        
                    </g>
                """)

        # border around whole svg
        self.rects.append(f"<rect x='0' y='0' width='{self.size[0] - 1}' height='{self.size[1] - 1}' style='fill:none;stroke-width:1;stroke:{css_hex(BLACK_PALE)}'/>")

    def coord_helper(self, note: SpecificNote) -> tuple[int, int, int, int, int, int]:
        """
        helper function which computes values for a given note

        Returns
        -------
        x: x coordinate of note rect
        w: width of note rect
        h: height of note rect
        c: color of note
        sx: x coordinate of square
        sy: x coordinate of square
        """
        c = self.note_colors.get(note, self.note_colors.get(note.abstract, note_color(note)))
        if note in self.white_notes:
            x = self.ww * self.white_notes.index(note)
            return x, self.ww, self.wh, c, (x + x + self.ww) // 2 - self.square_size // 2, self.wh - self.square_size - 5
        elif note in self.black_notes:
            x = self.ww * self.white_notes.index(note + 1) - self.bw // 2
            return x, self.bw, self.bh, c, x - self.square_size // 2, self.bh - self.square_size - 3
        else:
            raise KeyError('unknown note')

    def __repr__(self):
        return 'Piano'

    @staticmethod
    def pretty_print(svg: str) -> str:
        tree = ElementTree.fromstring(svg)
        ElementTree.indent(tree, level=0)
        return ElementTree.tostring(tree, encoding='unicode')

    def _repr_svg_(self):
        rects = '\n'.join(self.rects)
        svg = f"""
        <svg width='{self.size[0]}' height='{self.size[1]}'>
        {rects}
        </svg>
        """
        return Piano.pretty_print(svg)
