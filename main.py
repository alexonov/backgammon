import multiprocessing as mp
import time
from collections import defaultdict
from pathlib import Path

from game.bot import Bot
from game.bot import heuristics_eval_func
from game.bot import random_eval_func
from game.components import Board
from game.components import Colors
from game.gui import TerminalGUI
from game.match import play_match
from game.match import save_moves


def position():
    # file = 'bearingoff_position.pos'
    file = 'test_position.pos'
    # file = 'rule_six_block_position.pos'

    with open(Path('data') / file, 'r') as f:
        data = f.readlines()
    board = Board()
    board.setup_position(data)
    gui = TerminalGUI()
    gui.show_board(board)


def main():
    moves, score = play_match(
        white=Bot(Colors.WHITE, eval_func=random_eval_func),
        black=Bot(Colors.BLACK, eval_func=heuristics_eval_func),
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


if __name__ == '__main__':
    main()
    # position()
    # compare_bots()
