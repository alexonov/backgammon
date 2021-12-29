from pytest import mark

from game.components import Board
from game.components import Colors
from game.components import SingleMove
from game.rules import rule_six_block


@mark.parametrize(
    'single_move, expected',
    [
        (SingleMove(Colors.WHITE, 1, 5), False),
        (SingleMove(Colors.WHITE, 12, 18), True),
    ],
)
def test_rule_six_block(single_move, expected):
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
    assert rule_six_block(board, single_move) == expected
