import random

from tqdm import tqdm

from game.bot import HeuristicsBot  # noqa
from game.bot import RandomBot
from game.components import Board
from game.components import Colors
from game.components import Dice
from game.rules import win_condition
from game.td_model import TDBot
from game.td_model import TDNardiModel


def test_bots(bot_type, num_games=10):
    board = Board()

    bots = {
        Colors.WHITE: bot_type(Colors.WHITE),
        Colors.BLACK: TDBot(Colors.BLACK),
    }

    scores = {Colors.WHITE: 0, Colors.BLACK: 0}

    print()
    print(f'Starting bot test for {num_games} games')

    pbar = tqdm(range(num_games))
    for i in pbar:

        def _run_game(dice, starting_color):
            board.reset()
            last_color = Colors.opponent(starting_color)

            while win_condition(board, last_color) is None:
                color_to_move = Colors.opponent(last_color)
                dice_roll = dice.throw()

                player_move = bots[color_to_move].find_a_move(board, dice_roll)

                # make move
                if player_move:
                    for m in player_move:
                        board.do_single_move(m)

                last_color = color_to_move

                pbar.set_postfix(
                    {
                        'games': i,
                        type(bots[Colors.WHITE]).__name__: scores[Colors.WHITE],
                        type(bots[Colors.BLACK]).__name__: scores[Colors.BLACK],
                    }
                )

            scores[last_color] += win_condition(board, last_color)

        seed = random.randint(1, 10000)
        _run_game(dice=Dice(seed=seed), starting_color=Colors.WHITE)
        _run_game(dice=Dice(seed=seed), starting_color=Colors.BLACK)

    print(
        f'{type(bots[Colors.WHITE]).__name__} vs {type(bots[Colors.BLACK]).__name__}: {scores[Colors.WHITE]}:{scores[Colors.BLACK]}'
    )


def equity():
    board = Board()
    board.reset()

    model = TDNardiModel()
    model.restore()

    board = Board.generate_from_position(['1[W15]', '13[B15]'])
    starting_equity = model.equity(board, Colors.WHITE)

    board.setup_position(['24[W1]', '7[B15]'])
    white_to_win_equity = model.equity(board, Colors.WHITE)

    board.setup_position(['24[W1]', '13[B15]'])
    white_to_mars_equity = model.equity(board, Colors.WHITE)

    board.setup_position(['12[B1]', '19[W15]'])
    black_to_win_equity = model.equity(board, Colors.BLACK)

    board.setup_position(['12[B1]', '1[W15]'])
    black_to_mars_equity = model.equity(board, Colors.BLACK)

    print(f'starting_equity : {starting_equity}')
    print(f'white_to_win_equity : {white_to_win_equity}')
    print(f'white_to_mars_equity : {white_to_mars_equity}')
    print(f'black_to_win_equity : {black_to_win_equity}')
    print(f'black_to_mars_equity : {black_to_mars_equity}')


if __name__ == '__main__':

    test_bots(RandomBot, 10)
    test_bots(HeuristicsBot, 10)
    equity()
