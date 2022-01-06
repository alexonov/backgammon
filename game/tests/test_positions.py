from pytest import mark

from game.components import Board
from game.components import Colors
from game.rules import find_complete_legal_moves
from game.rules import SingleMove
from game.tests.utils import assert_no_duplicated_moves


@mark.parametrize(
    'position, color, dice_roll, expected_move, result',
    [
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            (2, 3),
            ['W:1->3', 'W:3->6'],
            True,
        ),  # simple first move
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            (6, 6),
            ['W:1->7', 'W:1->7', 'W:1->7', 'W:1->7'],
            False,
        ),  # first move 6,6
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            (3, 3),
            ['W:1->4', 'W:1->4', 'W:1->4', 'W:4->7'],
            False,
        ),  # first move 3,3
        (
            ['1[W15]', '13[B15]'],
            Colors.WHITE,
            (3, 3),
            ['W:1->4', 'W:4->7', 'W:1->4', 'W:4->7'],
            True,
        ),  # first move 3,3
        (
            ['1[W13]', '2[W1]', '13[B13]', '16[W1]', '18[B1]', '20[B1]'],
            Colors.BLACK,
            (4, 4),
            ['B:8->12', 'B:6->10', 'B:1->5', 'B:5->9'],
            True,
        ),  # bug
        (
            ['12[B1]', '24[W1]'],
            Colors.BLACK,
            (2, 6),
            ['B:24->30'],
            True,
        ),  # bug: bearing off single checker, with the highest die
        (
            ['12[B1]', '24[W1]'],
            Colors.BLACK,
            (2, 6),
            ['B:24->26'],
            False,
        ),  # bug: bearing off single checker, with the highest die
        (
            ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]', '9[B1]'],
            Colors.WHITE,
            (2, 6),
            ['W:1->7'],
            True,
        ),  # moving single checker, with the highest die
        (
            ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]', '9[B1]'],
            Colors.WHITE,
            (2, 6),
            ['W:1->3'],
            False,
        ),  # moving single checker, with the highest die
        (
            ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]'],
            Colors.WHITE,
            (2, 6),
            ['W:1->3', 'W:3->9'],
            True,
        ),  # play both dice when possible
        (
            ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]'],
            Colors.WHITE,
            (2, 6),
            ['W:1->3'],
            False,
        ),  # play both dice when possible
        (
            [
                '1[W2]',
                '2[B1]',
                '3[B1]',
                '4[W1]',
                '5[W1]',
                '6[B1]',
                '7[B1]',
                '9[W3]',
                '10[W3]',
                '11[B1]',
                '12[B2]',
                '14[B1]',
                '15[B2]',
                '16[B1]',
                '19[W3]',
                '20[B1]',
                '21[B2]',
                '22[B1]',
                '23[W1]',
                '24[W1]',
            ],
            Colors.BLACK,
            (5, 5),
            ['W:1->3'],
            False,
        ),  # double, long time to find moves
        (
            [
                '1[W11]',
                '8[W1]',
                '11[W3]',
                '13[B10]',
                '14[B1]',
                '16[B1]',
                '21[B1]',
                '22[B1]',
                '23[B1]',
            ],
            Colors.WHITE,
            (5, 5),
            ['W:1->6', 'W:6->11', 'W:6->11'],
            False,
        ),  # bug
        (
            [
                '18[W1]',
                '19[W1]',
                '22[W2]',
                '23[W1]',
                '24[W5]',
            ],
            Colors.WHITE,
            (1, 2),
            ['W:24->25', 'W:23->25'],
            False,
        ),  # bug
        (
            [
                '11[B1]',
                '12[B1]',
            ],
            Colors.BLACK,
            (3, 5),
            ['B:24->27', 'B:23->28'],
            True,
        ),  # bug
    ],
)
def test_find_complete_legal_moves_details(
    position, color, dice_roll, expected_move, result
):
    board = Board()
    board.setup_position(position)

    moves = find_complete_legal_moves(board, color, dice_roll)
    assert_no_duplicated_moves(moves)

    expected_move = [SingleMove.generate_from_str(m) for m in expected_move]
    assert (expected_move in moves) == result
