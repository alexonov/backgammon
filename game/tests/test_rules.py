from pytest import mark

from game.components import Board
from game.components import Colors
from game.components import SingleMove
from game.rules import find_complete_legal_moves
from game.rules import rule_six_block


@mark.parametrize(
    'move, expected',
    [
        ([SingleMove(Colors.WHITE, 1, 2), SingleMove(Colors.WHITE, 2, 5)], False),
        ([SingleMove(Colors.WHITE, 12, 15), SingleMove(Colors.WHITE, 15, 18)], True),
    ],
)
def test_rule_six_block(move, expected):
    board = Board()
    position = [
        '1[W5]',
        '2[W1]',
        '3[W1]',
        '4[W1]',
        '6[W1]',
        '12[W3]',
        '13[B10]',
        '14[W1]',
        '15[W1]',
        '16[W1]',
        '17[W1]',
        '19[W1]',
        '20[W1]',
        '22[B1]',
    ]
    board.setup_position(position)
    assert rule_six_block(board, move) == expected


@mark.parametrize(
    'color, dice, expected',
    [
        (Colors.WHITE, (1, 2), 26),
        (Colors.WHITE, (3, 3), 1162),
        (Colors.BLACK, (2, 6), 2),
        (Colors.BLACK, (2, 3), 1),
    ],
)
def test_find_complete_legal_moves(color, dice, expected):
    board = Board()
    position = [
        '1[W2]',
        '7[B1]',
        '5[W1]',
        '9[W1]',
        '10[W1]',
        '11[B2]',
        '13[W2]',
        '14[W2]',
        '23[W3]',
    ]
    board.setup_position(position)
    moves = find_complete_legal_moves(board, color, dice)
    assert len(moves) == expected
