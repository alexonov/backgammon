import json
import random
import uuid
from pathlib import Path
from timeit import default_timer as timer

import numpy as np
from tqdm import tqdm

from game.bot import HeuristicsBot  # noqa
from game.bot import RandomBot
from game.components import Board
from game.components import Colors
from game.components import Dice
from game.rules import win_condition
from game.td_model import TDBot


BENCHMARK_PATH = 'data/benchmarks'


def benchmark_move_time(num_games=10, top_n=10):
    dice = Dice()
    board = Board()
    bots = {color: RandomBot(color) for color in Colors.colors}
    # bots = {color: TDBot(color) for color in Colors.colors}

    print()
    print(f'Starting benchmark for {num_games} games')

    # only store top_n
    boards = []
    moves = []
    times = []
    min_time = -np.inf

    num_moves = 0

    pbar = tqdm(range(num_games))
    for i in pbar:
        board.reset()

        # randomly select who starts
        starting_color = random.choice([Colors.WHITE, Colors.BLACK])

        last_color = Colors.opponent(starting_color)

        while win_condition(board, last_color) is None:
            color_to_move = Colors.opponent(last_color)
            dice_roll = dice.throw()

            start = timer()
            player_move = bots[color_to_move].find_a_move(board, dice_roll)
            end = timer()

            move_time = end - start

            # check if we have bigger time
            if move_time > min_time or len(times) < top_n:
                if len(times) > top_n:
                    # remove move with min time
                    ind_to_remove = np.argmin(times)
                    del boards[ind_to_remove]
                    del moves[ind_to_remove]
                    del times[ind_to_remove]
                boards.append(board.export_position())
                moves.append(f'{color_to_move}{dice_roll}')
                times.append(move_time)
                min_time = min(times)

            # make move
            if player_move:
                for m in player_move:
                    board.do_single_move(m)

            last_color = color_to_move

            num_moves += 1

            pbar.set_postfix(
                {
                    'games': i,
                    'max_time': max(times),
                    'num_moves': num_moves,
                }
            )

    return [
        {'board': b, 'move': str(m), 'time': t} for b, m, t in zip(boards, moves, times)
    ]


def run_benchmark_move_time():
    num_games = 10
    top_n = 10

    report = benchmark_move_time(num_games, top_n)

    filename = f'top_{top_n}_from_{num_games}_games_{str(uuid.uuid4())}.json'

    with open(Path(BENCHMARK_PATH) / filename, 'w') as f:
        f.write(json.dumps(report))


def debug_move():
    import logging

    logging.basicConfig(level=logging.DEBUG)

    position = [
        '1[W2]',
        '2[B2]',
        '3[W1]',
        '6[W2]',
        '9[B2]',
        '10[W1]',
        '11[B4]',
        '12[W1]',
        '13[B2]',
        '14[B1]',
        '15[W1]',
        '16[W1]',
        '17[W1]',
        '18[B2]',
        '19[W1]',
        '20[B1]',
        '21[W1]',
        '22[W3]',
        '23[B1]',
    ]
    board = Board.generate_from_position(position)
    dice_roll = (2, 2)
    color = Colors.WHITE
    bot = TDBot(color)

    start = timer()
    move = bot.find_a_move(board, dice_roll)
    end = timer()

    print(f'{end - start} secs: move {move}')


if __name__ == '__main__':
    # run_benchmark_move_time()
    debug_move()
