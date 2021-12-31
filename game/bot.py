import random
from functools import partial
from typing import Callable

from game.components import Board
from game.components import SingleMove
from game.rules import find_complete_legal_moves


def dummy_eval_func(board: Board, moves: list[list[SingleMove]]) -> float:
    """
    dummy evaluation function - assigns random rank
    larger the rank the better
    """
    return random.random()


class Bot:
    def __init__(self, color: str, eval_func: Callable = dummy_eval_func):
        self.eval_func = eval_func
        self.color = color

    def find_a_move(self, board, dice_roll) -> list[SingleMove]:
        moves = find_complete_legal_moves(board, self.color, dice_roll)

        eval_func = partial(self.eval_func, board)

        # greater the rank the better
        moves_ranked = sorted(moves, key=eval_func)

        try:
            best_move = moves_ranked[-1]
        except IndexError:
            best_move = []

        return best_move
