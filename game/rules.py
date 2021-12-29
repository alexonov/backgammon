import copy

from .components import Board, SingleMove, Colors


def is_single_move_legal(board: Board, color: str, move: SingleMove):
    """
    checks if move can be legally made
    1. not blocking 6 in a row (unless there's a checker in front)
    2. bearing off only allowed if all are ot home
    3. if bearing off overshooting allowed only if there is no other not-bearing-off move
    4. only one take from the head
    5. rule of complete move (use both dice when possible)
    """
    assert board.is_single_move_possible(move), 'Move is not possible'

    # use fake board to make the move and check if it breaks rules
    fake_board = copy.deepcopy(board)

    # 1. blocks of 6 and over only allowed if opponent has a checker in front
    # a. make a fake move
    fake_board.do_single_move(move)

    # b. check if

