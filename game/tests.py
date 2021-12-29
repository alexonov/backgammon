from pytest import mark

from .components import Board, Colors, MIN_POSITION, MAX_POSITION
from .components import convert_coordinates
from .gui import pad_number


@mark.parametrize(
    'number, length, expected',
    [
        (1, 2, '01'),
        (11, 1, '11'),
        (123, 2, '123'),
        (1, 5, '00001')
    ]
)
def test_pad_number(number, length, expected):
    assert pad_number(number, length) == expected


def test_convert_coordinates():
    white = list(range(MIN_POSITION, MAX_POSITION + 1))
    black = [convert_coordinates(i) for i in white]
    expected = list(range(MIN_POSITION + 12, MAX_POSITION + 1)) + list(range(MIN_POSITION, MIN_POSITION + 12))
    assert expected == black


@mark.parametrize(
    'color, position, expected',
    [
        (Colors.WHITE, 1, 1),
        (Colors.WHITE, 12, 12),
        (Colors.WHITE, 24, 24),
        (Colors.BLACK, 1, 13),
        (Colors.BLACK, 12, 24),
        (Colors.BLACK, 24, 12),
    ]
)
def test_board_lookup(color, position, expected):
    board = Board()
    slot = board.get_slot(color, position)
    assert slot.real_position == expected

