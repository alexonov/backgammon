import random
from functools import partial
from typing import Callable

from game.components import Board
from game.components import MAX_POSITION
from game.components import MIN_POSITION
from game.components import SingleMove
from game.rules import find_complete_legal_moves


def random_eval_func(board: Board, moves: list[SingleMove]) -> float:
    """
    dummy evaluation function - assigns random rank
    larger the rank the better
    """
    return random.random()


def heuristics_eval_func(board: Board, moves: list[SingleMove]) -> float:
    """
    ranks moves based on a set of basic heuristics

    - prefer moves that create blocks of 6 or higher
    - prefer moves that create blocks of 2 or higher
    - prefer moves that take from head
    - prefer moves that minimize pip count
    - prefer bearing off moves
    - prefer moves that spread out checkers
    - prefer moves with smaller mean and median num checkers per slot

    all have equal importance
    """

    color = moves[0].color

    fake_board = board.copy_board()
    for sm in moves:
        fake_board.do_single_move(sm)

    # evaluate heuristic 1: prefer moves that create blocks of 6 or higher
    blocks_of_six = fake_board.find_blocks_min_length(color, 6)
    h_blocks_six = len(blocks_of_six)

    # evaluate heuristic 2: prefer moves that create blocks of 2 or higher
    blocks_of_two = fake_board.find_blocks_min_length(color, 2)
    h_blocks_two = len(blocks_of_two)

    # evaluate heuristic 3: prefer moves that take from head
    h_from_head = -fake_board.num_on_head(color) / 15

    # evaluate heuristic 4: prefer moves that minimize pip count
    max_pip_count = ((MAX_POSITION + 1) - MIN_POSITION) * 15
    h_pip_count = -fake_board.pip_count(color) / max_pip_count

    # evaluate heuristic 5: prefer bearing off moves
    h_bear_off = fake_board.num_on_tray(color)

    # checkers distribution
    stats = fake_board.checkers_distribution(color)
    h_ratio = stats['spread_ratio']
    h_mean = -stats['mean']
    h_median = -stats['median']
    h_distance = -stats['mean_distance']

    return (
        h_blocks_six
        + h_blocks_two
        + h_from_head
        + h_pip_count
        + h_bear_off
        + h_ratio
        + h_mean
        + h_median
        + h_distance
    )


class Bot:
    def __init__(self, color: str, eval_func: Callable = random_eval_func):
        self._eval_func = eval_func
        self.color = color

    def find_a_move(self, board, dice_roll) -> list[SingleMove]:
        moves = find_complete_legal_moves(board, self.color, dice_roll)

        eval_func = partial(self._eval_func, board)

        # greater the evaluation the better
        moves_ranked = sorted(moves, key=eval_func)

        try:
            best_move = moves_ranked[-1]
        except IndexError:
            best_move = []

        return best_move


class RandomBot(Bot):
    def __init__(self, color: str):
        super().__init__(color, random_eval_func)


class HeuristicsBot(Bot):
    def __init__(self, color: str):
        super().__init__(color, heuristics_eval_func)
