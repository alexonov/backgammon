from numpy.testing import assert_almost_equal
from pytest import mark

from game.components import Board
from game.components import Colors
from game.components import convert_coordinates
from game.components import MAX_POSITION
from game.components import MIN_POSITION
from game.components import SingleMove
from game.gui import pad_number


@mark.parametrize(
    'number, length, expected',
    [(1, 2, '01'), (11, 1, '11'), (123, 2, '123'), (1, 5, '00001')],
)
def test_pad_number(number, length, expected):
    assert pad_number(number, length) == expected


def test_convert_coordinates():
    white = list(range(MIN_POSITION, MAX_POSITION + 1))
    black = [convert_coordinates(i) for i in white]
    expected = list(range(MIN_POSITION + 12, MAX_POSITION + 1)) + list(
        range(MIN_POSITION, MIN_POSITION + 12)
    )
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
    ],
)
def test_board_lookup(color, position, expected):
    board = Board()
    slot = board.get_slot(color, position)
    assert slot.real_position == expected


@mark.parametrize(
    'color, point, expected',
    [
        (Colors.WHITE, 0, 6),
        (Colors.WHITE, 2, 4),
        (Colors.WHITE, 10, 3),
        (Colors.WHITE, 24, 0),
        (Colors.BLACK, 13, 3),
        (Colors.BLACK, 20, 2),
    ],
)
def test_num_checkers_after_position(color, point, expected):
    board = Board()
    position = ['1[W2]', '2[B1]', '5[W1]', '11[B2]', '23[W3]']
    board.setup_position(position)

    num = board.num_checkers_after_position(color, point)
    assert num == expected


@mark.parametrize(
    'position, min_length, expected',
    [
        (['1[W1]', '2[W1]', '3[W1]'], 2, 1),
        (['1[W1]', '2[W1]', '3[W1]'], 3, 1),
        (['1[W1]', '2[W1]', '3[W1]', '4[W1]', '5[W1]'], 4, 1),
        (['1[W1]', '2[W1]', '3[W1]', '4[B1]', '5[W1]'], 4, 0),
        (['1[W1]', '2[W3]', '3[W1]', '4[B1]', '5[W1]', '6[W2]'], 2, 2),
    ],
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
    ],
)
def test_single_move_possible(single_move, expected):
    board = Board()
    position = ['1[W2]', '2[B1]', '5[W1]', '23[W3]']
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
    ],
)
def test_find_possible_moves(color, die_roll, expected):
    board = Board()
    position = ['1[W2]', '2[B1]', '5[W1]', '11[B2]', '23[W3]']
    board.setup_position(position)
    moves = board.find_possible_moves(color, die_roll)
    assert len(moves) == expected


def test_export_position():
    board = Board()
    position = ['0[B2]', '1[W2]', '2[B1]', '5[W1]', '11[B2]', '23[W3]', '25[W1]']
    board.setup_position(position)
    exported = board.export_position()
    assert exported == position


@mark.parametrize(
    'position, move, expected_position',
    [
        (['1[W5]'], SingleMove(Colors.WHITE, 1, 5), ['1[W4]', '5[W1]']),
        (['4[W1]'], SingleMove(Colors.WHITE, 4, 7), ['7[W1]']),
        (['22[W5]'], SingleMove(Colors.WHITE, 22, 25), ['22[W4]', '25[W1]']),
        (['22[W5]'], SingleMove(Colors.WHITE, 22, 27), ['22[W4]', '25[W1]']),
        (['1[B5]'], SingleMove(Colors.BLACK, 13, 17), ['1[B4]', '5[B1]']),
        (['4[B1]'], SingleMove(Colors.BLACK, 16, 19), ['7[B1]']),
        (['22[B5]'], SingleMove(Colors.BLACK, 10, 14), ['2[B1]', '22[B4]']),
        (['11[B5]'], SingleMove(Colors.BLACK, 23, 25), ['0[B1]', '11[B4]']),
        (['11[B5]'], SingleMove(Colors.BLACK, 23, 28), ['0[B1]', '11[B4]']),
    ],
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


@mark.parametrize(
    'position, turn, ind, expected',
    [
        (['1[W15]', '13[B15]'], Colors.WHITE, 0, 1),
        (['1[W15]', '13[B15]'], Colors.WHITE, 1, 1),
        (['1[W15]', '13[B15]'], Colors.WHITE, 2, 6.5),
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            24 * Board.BITS_PER_COLOR_SLOT + 12 * Board.BITS_PER_COLOR_SLOT,
            1,
        ),
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            24 * Board.BITS_PER_COLOR_SLOT + 12 * Board.BITS_PER_COLOR_SLOT + 1,
            1,
        ),
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            24 * Board.BITS_PER_COLOR_SLOT * 2 + 2,
            1,
        ),
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            24 * Board.BITS_PER_COLOR_SLOT * 2 + 2 + 1,
            0,
        ),
        (['5[W4]'], Colors.WHITE, 12, 1),
        (['5[W4]'], Colors.WHITE, 13, 1),
        (['5[W4]'], Colors.WHITE, 14, 1),
    ],
)
def test_encode(position, turn, ind, expected):
    board = Board()
    board.setup_position(position)
    encoded = board.encode(turn)
    assert_almost_equal(encoded[ind], expected, decimal=3)


@mark.parametrize(
    'position, color, expected',
    [
        (
            [
                '18[W1]',
                '19[W1]',
                '22[W2]',
                '23[W1]',
                '24[W5]',
            ],
            Colors.WHITE,
            False,
        ),
        (
            [
                '18[B1]',
                '19[W1]',
                '22[W2]',
                '23[W1]',
                '24[W5]',
            ],
            Colors.WHITE,
            True,
        ),
    ],
)
def test_has_all_checkers_home(position, color, expected):
    board = Board.generate_from_position(position)
    assert board.has_all_checkers_home(color) == expected


@mark.parametrize(
    'position, color, key, expected',
    [
        (['11[B1]', '12[B1]'], Colors.BLACK, 'mean_distance', 1),
        (['1[W15]', '13[B15]'], Colors.BLACK, 'mean_distance', 0),
    ],
)
def test_checkers_distribution(position, color, key, expected):
    board = Board.generate_from_position(position)
    stats = board.checkers_distribution(color)
    assert stats[key] == expected
