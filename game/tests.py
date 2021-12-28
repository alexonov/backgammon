from pytest import mark

from .components import Board
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
    white = list(range(24))
    black = [convert_coordinates(i) for i in white]
    expected = list(range(12, 24)) + list(range(12))
    assert expected == black


def test_board_setup():
    board = Board()

    assert len(board.slots) == 24

    board.reset()
