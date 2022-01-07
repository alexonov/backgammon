import logging
import multiprocessing as mp  # noqa
import random
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from keras.layers import Dense
from keras.layers import Input
from keras.models import Model
from tqdm import tqdm

from game.bot import Bot
from game.bot import HeuristicsBot
from game.bot import RandomBot
from game.components import Board
from game.components import Colors
from game.components import Dice
from game.components import SingleMove
from game.rules import find_complete_legal_moves
from game.rules import has_won
from game.rules import win_condition


class HillClimberModel:
    """
    based on https://proceedings.neurips.cc/paper/1996/file/459a4ddcb586f24efd9395aa7662bc7c-Paper.pdf
    """

    _LOGS_PATH = Path('data') / 'logs' / 'HillClimberModel'
    _CHECKPOINTS_PATH = Path('data') / 'checkpoints' / 'HillClimberModel'

    def __init__(self, restore=False):
        self.model = self.generate_blank_model()

        self.weight_shape = [w.shape for w in self.model.trainable_variables]
        self.total_weights = sum(tf.reduce_prod(s) for s in self.weight_shape)

        self._CHECKPOINTS_PATH.mkdir(parents=True, exist_ok=True)
        self._LOGS_PATH.mkdir(parents=True, exist_ok=True)

        self.writer = tf.summary.create_file_writer(str(self._LOGS_PATH))

        self.iteration = tf.Variable(
            0, trainable=False, name='iteration', dtype='int64'
        )

        self.checkpoint = tf.train.Checkpoint(
            iteration=self.iteration,
            model=self.model,
        )

        self.manager = tf.train.CheckpointManager(
            self.checkpoint, self._CHECKPOINTS_PATH, max_to_keep=3
        )

        if restore:
            self.restore()

    def backup(self):
        self.manager.save()

    def restore(self):
        self.checkpoint.restore(self.manager.latest_checkpoint)
        if self.manager.latest_checkpoint:
            print(f'Restored from {self.manager.latest_checkpoint}')
        else:
            print('Initializing from scratch.')

    @staticmethod
    def generate_blank_model():
        init_with_zeros = tf.keras.initializers.Zeros()

        inputs = Input(shape=Board.encode_shape, name='input')
        hidden = Dense(
            80,
            activation='sigmoid',
            name='hidden_layer',
            kernel_initializer=init_with_zeros,
        )(inputs)
        output = Dense(
            1, activation='sigmoid', name='output', kernel_initializer=init_with_zeros
        )(hidden)
        model = Model(inputs=inputs, outputs=output)
        return model

    def generate_noise(self, stddev=0.05):
        noise = [
            tf.random.normal(
                shape,
                mean=0.0,
                stddev=stddev,
                dtype=tf.dtypes.float32,
                seed=None,
                name=None,
            )
            for shape in self.weight_shape
        ]
        return noise

    def generate_mutant(self, stddev=0.05):
        noise = self.generate_noise(stddev)
        mutant_weights = [w + n for w, n in zip(self.model.trainable_variables, noise)]
        model = self.generate_blank_model()
        for i, w in enumerate(mutant_weights):
            model.trainable_variables[i].assign(w)
        return model

    def absorb_mutant(self, mutant):
        # champion := 0.95*champion + 0.05*challenger
        for i, w in enumerate(self.model.trainable_variables):
            self.model.trainable_variables[i].assign(
                0.95 * w + 0.05 * mutant.trainable_variables[i]
            )

    @classmethod
    def find_move_for_model(
        cls, model, color: str, board: Board, dice_roll: tuple[int, int]
    ):
        def _get_prob(out):
            if color == Colors.WHITE:
                return out[0]
            else:
                return 1 - out[0]

        start = time.time()
        moves = find_complete_legal_moves(board, color, dice_roll)
        max_move = None
        max_prob = -np.inf

        for move in moves:
            afterstate = board.copy_board()
            for sm in move:
                afterstate.do_single_move(sm)

            state = afterstate.encode(Colors.opponent(color))
            output = model(state[np.newaxis])

            prob = _get_prob(output)

            if prob > max_prob:
                max_prob = prob
                max_move = move

        duration = time.time() - start
        logging.debug(
            f'playing move {max_move} [winning prob = {max_prob}] [total time = {duration}]'
        )
        return max_move

    def find_move(self, color: str, board: Board, dice_roll: tuple[int, int]):
        return self.find_move_for_model(self.model, color, board, dice_roll)

    def is_mutant_good(self, mutant):
        """
        plays a pair of games with mutant.
        same dice is used, colors are switched
        """
        NUM_CORE = 4  # noqa
        NUM_GAMES = 2  # (this will be played 2 times with roles switched)

        dices = [Dice(seed=random.randint(1, 10000)) for _ in range(NUM_GAMES)]

        params = []
        for d in dices:
            starting_color = random.choice(Colors.colors)
            params.append(
                (self.model, Colors.WHITE, mutant, Colors.BLACK, starting_color, d)
            )
            params.append(
                (self.model, Colors.BLACK, mutant, Colors.WHITE, starting_color, d)
            )

        # with mp.Pool(processes=NUM_CORE) as pool:
        #     results = pool.starmap(
        #         play_with_mutant,
        #         params
        #     )
        results = [play_with_mutant(*p) for p in params]

        mutant_num_wins = 0
        for r in results:
            mutant_num_wins += min(r, 1)

        return mutant_num_wins >= NUM_GAMES * 2 - 1

    def train(self, num_iterations):
        test_every_n_iteration = 100
        print(f'\nStarting training cycle for {num_iterations} episodes')

        num_absorbed = 0
        pbar = tqdm(range(num_iterations))
        for i in pbar:

            if i % test_every_n_iteration == 0 and i > 0:
                self.test_equity()
                self.test_against_random()
                self.test_against_heuristics()

            mutant = self.generate_mutant()
            if self.is_mutant_good(mutant):
                self.absorb_mutant(mutant)
                num_absorbed += 1

            pbar.set_postfix({'absorbed': num_absorbed})
            self.iteration.assign_add(1)
            self.backup()

    def equity(self, board: Board, turn: str):
        state = board.encode(turn)
        output = self.model(state[np.newaxis])
        return output.numpy()[0]

    def test_equity(self):
        board = Board.generate_from_position(['1[W15]', '13[B15]'])
        starting_equity = self.equity(board, Colors.WHITE)

        board.setup_position(['24[W1]', '7[B15]'])
        white_to_win_equity = self.equity(board, Colors.WHITE)

        board.setup_position(['24[W1]', '13[B15]'])
        white_to_mars_equity = self.equity(board, Colors.WHITE)

        board.setup_position(['12[B1]', '19[W15]'])
        black_to_win_equity = self.equity(board, Colors.BLACK)

        board.setup_position(['12[B1]', '1[W15]'])
        black_to_mars_equity = self.equity(board, Colors.BLACK)

        with self.writer.as_default():
            tf.summary.scalar(
                'tests/equity_starting',
                starting_equity[0],
                step=self.iteration,
            )
            tf.summary.scalar(
                'tests/equity_white_to_win',
                white_to_win_equity[0],
                step=self.iteration,
            )
            tf.summary.scalar(
                'tests/equity_white_to_mars',
                white_to_mars_equity[0],
                step=self.iteration,
            )
            tf.summary.scalar(
                'tests/equity black_to_win',
                black_to_win_equity[0],
                step=self.iteration,
            )
            tf.summary.scalar(
                'tests/equity_black_to_mars',
                black_to_mars_equity[0],
                step=self.iteration,
            )
            self.writer.flush()

    def test_against_bot(self, bot: Bot, num_games=50):
        scores = {Colors.WHITE: 0, Colors.BLACK: 0}
        games_won = {Colors.WHITE: 0, Colors.BLACK: 0}

        def _run_game(dice, starting_color):
            last_color = Colors.opponent(starting_color)
            board.reset()

            while win_condition(board, last_color) is None:
                color_to_move = Colors.opponent(last_color)
                dice_roll = dice.throw()

                if color_to_move == bot.color:
                    player_move = bot.find_a_move(board, dice_roll)
                else:
                    player_move = self.find_move(color_to_move, board, dice_roll)

                # make move
                if player_move:
                    for m in player_move:
                        board.do_single_move(m)

                last_color = color_to_move

            scores[last_color] += win_condition(board, last_color)
            games_won[last_color] += min(1, win_condition(board, last_color))

        board = Board()

        for i in range(num_games):
            seed = random.randint(1, 10000)
            _run_game(Dice(seed=seed), Colors.WHITE)
            _run_game(Dice(seed=seed), Colors.BLACK)

        return (
            games_won[Colors.opponent(bot.color)] / (num_games * 2),
            scores[Colors.opponent(bot.color)] / scores[bot.color],
        )

    def test_against_random(self, num_games=10):
        bot = RandomBot(Colors.WHITE)
        win_ratio, score_ratio = self.test_against_bot(bot, num_games)
        with self.writer.as_default():
            tf.summary.scalar('tests/random_win_ratio', win_ratio, step=self.iteration)
            tf.summary.scalar(
                'tests/random_score_ratio', score_ratio, step=self.iteration
            )
            self.writer.flush()

    def test_against_heuristics(self, num_games=10):
        bot = HeuristicsBot(Colors.WHITE)
        win_ratio, score_ratio = self.test_against_bot(bot, num_games)
        with self.writer.as_default():
            tf.summary.scalar(
                'tests/heuristics_win_ratio', win_ratio, step=self.iteration
            )
            tf.summary.scalar(
                'tests/heuristics_score_ratio', score_ratio, step=self.iteration
            )
            self.writer.flush()


def play_with_mutant(
    champion, champion_color, mutant, mutant_color, starting_color, dice
):
    board = Board()
    board.reset()

    models = {champion_color: champion, mutant_color: mutant}

    last_color = Colors.opponent(starting_color)
    while win_condition(board, last_color) is None:
        color_to_move = Colors.opponent(last_color)
        dice_roll = dice.throw()

        move = HillClimberModel.find_move_for_model(
            models[color_to_move], color_to_move, board, dice_roll
        )

        # make move
        if move:
            for m in move:
                board.do_single_move(m)

        last_color = color_to_move

    return has_won(board, mutant_color)


class HillClimberBot:
    def __init__(self, color: str):
        model = HillClimberModel()
        model.restore()
        self._model = model
        self._color = color

    def find_a_move(self, board, dice_roll) -> list[SingleMove]:
        return self._model.find_move(self._color, board, dice_roll)


if __name__ == '__main__':
    model = HillClimberModel(restore=True)
    model.train(5000)
