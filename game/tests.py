from pytest import mark

from .components import Board, Colors, MIN_POSITION, MAX_POSITION, SingleMove
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
        (Colors.WHITE, 25, 25),
        (Colors.BLACK, 25, 0),
    ]
)
def test_board_lookup(color, position, expected):
    board = Board()
    slot = board.get_slot(color, position)
    assert slot.real_position == expected


@mark.parametrize(
    'position, min_length, expected',
    [
        (['1[W1]', '2[W1]', '3[W1]'], 2, 1),
        (['1[W1]', '2[W1]', '3[W1]'], 3, 1),
        (['1[W1]', '2[W1]', '3[W1]', '4[W1]', '5[W1]'], 4, 1),
        (['1[W1]', '2[W1]', '3[W1]', '4[B1]', '5[W1]'], 4, 0),
        (['1[W1]', '2[W3]', '3[W1]', '4[B1]', '5[W1]', '6[W2]'], 2, 2),
    ]
)
def test_num_blocks(position, min_length, expected):
    board = Board()
    board.setup_position(position)
    blocks = board.find_blocks_min_length(Colors.WHITE, min_length)
    assert len(blocks) == expected


@mark.parametrize(
    'single_move, expected',
    [
        (SingleMove(Colors.WHITE, 1, 2), False),
        (SingleMove(Colors.WHITE, 1, 5), True),
        (SingleMove(Colors.WHITE, 23, 25), True),
        (SingleMove(Colors.BLACK, 14, 19), True),
        (SingleMove(Colors.BLACK, 23, 24), False),
        (SingleMove(Colors.WHITE, 3, 4), False),
    ]
)
def test_single_move_possible(single_move, expected):
    board = Board()
    position = [
        '1[W2]',
        '2[B1]',
        '5[W1]',
        '23[W3]'
    ]
    board.setup_position(position)
    assert board.is_single_move_possible(single_move) == expected


@mark.parametrize(
    'color, die_roll, expected',
    [
        (Colors.WHITE, 1, 2),
        (Colors.WHITE, 3, 3),
        (Colors.WHITE, 6, 2),
        (Colors.BLACK, 1, 2),
        (Colors.BLACK, 3, 1),
        (Colors.BLACK, 4, 2),
    ]
)
def test_find_possible_moves(color, die_roll, expected):
    board = Board()
    position = [
        '1[W2]',
        '2[B1]',
        '5[W1]',
        '11[B2]',
        '23[W3]'
    ]
    board.setup_position(position)
    moves = board.find_possible_moves(color, die_roll)
    assert len(moves) == expected


def test_export_position():
    board = Board()
    position = [
        '1[W2]',
        '2[B1]',
        '5[W1]',
        '11[B2]',
        '23[W3]'
    ]
    board.setup_position(position)
    exported = board.export_position()
    assert exported == position


@mark.parametrize(
    'position, move, expected_position',
    [
        (['1[W5]'], SingleMove(Colors.WHITE, 1, 5), ['1[W4]', '5[W1]']),
        (['4[W1]'], SingleMove(Colors.WHITE, 4, 7), ['7[W1]']),
        (['22[W5]'], SingleMove(Colors.WHITE, 22, 25), ['22[W4]']),
        (['1[B5]'], SingleMove(Colors.BLACK, 13, 17), ['1[B4]', '5[B1]']),
        (['4[B1]'], SingleMove(Colors.BLACK, 16, 19), ['7[B1]']),
        (['22[B5]'], SingleMove(Colors.BLACK, 10, 14), ['2[B1]', '22[B4]']),
        (['11[B5]'], SingleMove(Colors.BLACK, 23, 25), ['11[B4]']),
    ]
)
def test_do_move(position, move, expected_position):
    board = Board()
    board.setup_position(position)
    board.do_single_move(move)

    new_position = board.export_position()
    assert new_position == expected_position

    board.undo_single_move(move)
    old_position = board.export_position()
    assert old_position == position




