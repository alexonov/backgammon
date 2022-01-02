from pytest import mark

from game.components import Board
from game.components import Colors
from game.components import SingleMove
from game.rules import find_complete_legal_moves
from game.rules import passes_rule_six_block


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
    assert passes_rule_six_block(board, move) == expected


@mark.parametrize(
    'color, position, moves, expected',
    [
        (
            Colors.BLACK,
            ['1[W13]', '2[W1]', '13[B13]', '16[W1]', '18[B1]', '20[B1]'],
            ['B:1->5', 'B:5->9'],
            True,
        )
    ],
)
def test_rule_six_block_bugs(color, position, moves, expected):
    board = Board()
    board.setup_position(position)
    moves = [SingleMove.generate_from_str(m) for m in moves]
    result = passes_rule_six_block(board, moves)
    assert result == expected


@mark.parametrize(
    'color, dice, expected',
    [
        (Colors.WHITE, (1, 2), 53),
        (Colors.WHITE, (3, 3), 1162),
        (Colors.BLACK, (2, 6), 4),
        (Colors.BLACK, (2, 3), 2),
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


@mark.parametrize(
    'position, color, dice_roll, expected_move, result',
    [
        # (
        #     ['1[W15]', '13[B15]'],
        #     Colors.WHITE,
        #     (2, 3),
        #     ['W:1->3', 'W:3->6'],
        #     True,
        # ),  # simple first move
        # (
        #     ['1[W15]', '13[B15]'],
        #     Colors.WHITE,
        #     (6, 6),
        #     ['W:1->7', 'W:1->7', 'W:1->7', 'W:1->7'],
        #     False,
        # ),  # first move 6,6
        # (
        #     ['1[W15]', '13[B15]'],
        #     Colors.WHITE,
        #     (3, 3),
        #     ['W:1->4', 'W:1->4', 'W:1->4', 'W:4->7'],
        #     False,
        # ),  # first move 3,3
        # (
        #     ['1[W15]', '13[B15]'],
        #     Colors.WHITE,
        #     (3, 3),
        #     ['W:1->4', 'W:1->4', 'W:4->7', 'W:4->7'],
        #     True,
        # ),  # first move 3,3
        # (
        #     ['1[W13]', '2[W1]', '13[B13]', '16[W1]', '18[B1]', '20[B1]'],
        #     Colors.BLACK,
        #     (4, 4),
        #     ['B:1->5', 'B:5->9', 'B:6->10', 'B:8->12'],
        #     True,
        # ),  # bug
        # (
        #     ['12[B1]', '24[W1]'],
        #     Colors.BLACK,
        #     (2, 6),
        #     ['B:24->30'],
        #     True,
        # ),  # bug: bearing off single checker, with the highest die
        # (
        #     ['12[B1]', '24[W1]'],
        #     Colors.BLACK,
        #     (2, 6),
        #     ['B:24->26'],
        #     False,
        # ),  # bug: bearing off single checker, with the highest die
        # (
        #     ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]', '9[B1]'],
        #     Colors.WHITE,
        #     (2, 6),
        #     ['W:1->7'],
        #     True,
        # ),  # moving single checker, with the highest die
        # (
        #     ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]', '9[B1]'],
        #     Colors.WHITE,
        #     (2, 6),
        #     ['W:1->3'],
        #     False,
        # ),  # moving single checker, with the highest die
        # (
        #     ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]'],
        #     Colors.WHITE,
        #     (2, 6),
        #     ['W:1->7', 'W:7->9'],
        #     True,
        # ),  # play both dice when possible
        # (
        #     ['1[W2]', '2[B1]', '4[B1]', '5[B1]', '6[B1]'],
        #     Colors.WHITE,
        #     (2, 6),
        #     ['W:1->3'],
        #     False,
        # ),  # play both dice when possible
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
    ],
)
def test_find_complete_legal_moves_details(
    position, color, dice_roll, expected_move, result
):
    board = Board()
    board.setup_position(position)
    moves = find_complete_legal_moves(board, color, dice_roll)
    expected_move = [SingleMove.generate_from_str(m) for m in expected_move]
    assert (expected_move in moves) == result
