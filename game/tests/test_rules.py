from pytest import mark

from game.components import Board
from game.components import Colors
from game.components import SingleMove
from game.gui import CompleteMove
from game.rules import find_complete_legal_moves
from game.rules import init_cache
from game.rules import passes_rule_six_block
from game.rules import remove_extra_from_head_moves
from game.tests.utils import assert_no_duplicated_moves


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
    init_cache(board)
    assert passes_rule_six_block(move) == expected


@mark.parametrize(
    'moves, allowed_num, expected',
    [
        # remove all subsequent moves
        (['W:1->6', 'W:1->6', 'W:6->11', 'W:6->11'], 1, ['W:1->6', 'W:6->11'])
    ],
)
def test_remove_extra_from_head(moves, allowed_num, expected):
    moves = [SingleMove.generate_from_str(m) for m in moves]
    filtered = remove_extra_from_head_moves(moves, allowed_num=allowed_num)
    expected = [SingleMove.generate_from_str(m) for m in expected]
    assert filtered == expected


@mark.parametrize(
    'color, position, moves, expected',
    [
        (
            Colors.BLACK,
            ['1[W13]', '2[W1]', '13[B13]', '16[W1]', '18[B1]', '20[B1]'],
            ['B:1->5', 'B:5->9'],
            True,
        ),
    ],
)
def test_rule_six_block_bugs(color, position, moves, expected):
    board = Board()
    board.setup_position(position)
    moves = [SingleMove.generate_from_str(m) for m in moves]

    init_cache(board)
    result = passes_rule_six_block(moves)
    assert result == expected


@mark.parametrize(
    'color, dice, expected',
    [
        (Colors.WHITE, (1, 2), 27),
        (Colors.WHITE, (3, 3), 105),
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
    assert_no_duplicated_moves(moves)


@mark.parametrize(
    'moves, color, dice_roll',
    [
        (
            [
                'B(2, 2): 1/3, 3/5, 5/7, 7/9',
                'W(5, 1): 1/2, 2/7',
                'B(6, 3): 1/4, 4/10',
                'W(1, 5): 1/2, 2/7',
                'B(2, 1): 1/2, 9/11',
                'W(2, 4): 7/11, 1/3',
                'B(3, 4): 1/4, 4/8',
                'W(5, 4): 3/8, 7/11',
                'B(1, 3): 8/9, 1/4',
            ],
            Colors.WHITE,
            (5, 5),
        )
    ],
)
def test_game_scenario(moves, color, dice_roll):
    board = Board()
    board.reset()
    for m in moves:
        complete_move = CompleteMove.generate_from_str(m)
        for sm in complete_move.moves:
            board.do_single_move(sm)

    next_moves = find_complete_legal_moves(board, color, dice_roll)

    assert_no_duplicated_moves(next_moves)

    # make sure all moves are doable
    for m in next_moves:
        fake_board = board.copy_board()
        for sm in m:
            fake_board.do_single_move(sm)

    assert True
