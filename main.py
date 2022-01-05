import multiprocessing as mp
import time
from collections import defaultdict
from pathlib import Path
from timeit import default_timer as timer

from game.bot import Bot
from game.bot import heuristics_eval_func
from game.bot import random_eval_func
from game.components import Board
from game.components import Colors
from game.gui import TerminalGUI
from game.match import play_match
from game.match import save_moves
from game.model.model import TDNardiModel
from game.rules import find_complete_legal_moves


def position():
    # file = 'bearingoff_position.pos'
    # file = 'test_position.pos'
    # file = 'rule_six_block_position.pos'
    # file = 'bug.pos'
    file = 'double_benchmark.pos'

    with open(Path('data') / 'board_positions' / file, 'r') as f:
        data = f.readlines()
    board = Board()
    board.setup_position(data)
    gui = TerminalGUI()
    gui.show_board(board)


def play_game():
    moves, score = play_match(
        white=Bot(Colors.WHITE, eval_func=random_eval_func),
        black=Bot(Colors.BLACK, eval_func=heuristics_eval_func),
        show_gui=True,
    )
    save_moves(moves)


def compare_bots(num_games=10):
    NUM_CORE = 10

    scores = defaultdict(int)

    bot_a = Bot(Colors.WHITE, eval_func=random_eval_func)
    bot_b = Bot(Colors.BLACK, eval_func=heuristics_eval_func)

    start_time = time.time()
    with mp.Pool(processes=NUM_CORE) as pool:
        results = pool.starmap(
            play_match, ((bot_a, bot_b, False) for _ in range(num_games))
        )

    elapsed_time = time.time() - start_time
    print(f'total time: {elapsed_time / 60} min')

    for r in results:
        _, game_result = r
        scores[game_result['winner']] += game_result['score']
    print(scores)


def train(num_games=1):
    model = TDNardiModel()
    model.train(num_games, restore=True)


def double_benchmark():
    pos = [
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
    ]
    board = Board()
    board.setup_position(pos)
    _ = find_complete_legal_moves(board, Colors.BLACK, (5, 5))


def benchmark(func):
    start = timer()
    func()
    end = timer()
    print(f'time taken for {func.__name__}: {end - start}')


if __name__ == '__main__':
    # play_game()
    # position()
    # compare_bots()

    train(5000)

    # benchmark(double_benchmark)
    #
    # board = Board()
    #
    # def copy_board():
    #     _ = copy.deepcopy(board)
    #
    # def export_board():
    #     _ = board.copy_board()
    #
    # benchmark(copy_board)
    # benchmark(export_board)
