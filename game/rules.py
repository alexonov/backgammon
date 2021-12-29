"""
Main rules:
    1. not blocking 6 in a row (unless there's a checker in front)
"""
import copy

from game.components import Board
from game.components import Colors
from game.components import convert_coordinates
from game.components import SingleMove


def rule_six_block(board: Board, move: SingleMove) -> bool:
    """
    not blocking 6 in a row (unless there's a checker in front)
    """
    fake_board = copy.deepcopy(board)
    fake_board.do_single_move(move)

    # check if there are 6-blocks after the move
    blocks = fake_board.find_blocks_min_length(move.color, 6)
    if len(blocks) == 0:
        return True

    opponent_color = Colors.WHITE if move.color == Colors.BLACK else Colors.BLACK

    # check each block if it can be legally allowed
    for b in blocks:
        # take last position
        last_position = b[-1]

        # convert it to opponent's coordinates
        last_position_opponent = convert_coordinates(last_position)
        num_checkers = fake_board.num_checkers_after_position(
            opponent_color, last_position_opponent
        )

        if num_checkers == 0:
            return False
    else:
        return True


def is_single_move_legal(board: Board, move: SingleMove):
    """
    checks if move can be legally made
    1. not blocking 6 in a row (unless there's a checker in front)
    2. bearing off only allowed if all are ot home
    3. if bearing off overshooting allowed only if there is no other not-bearing-off move
    4. only one take from the head
    5. rule of complete move (use both dice when possible)
    """
    assert board.is_single_move_possible(move), 'Move is not possible'
