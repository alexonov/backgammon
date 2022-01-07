import logging
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
from game.rules import win_condition


class TDNardiModel:
    _LAMBDA = 0
    _ALPHA = 0.01

    _CHECKPOINTS_PATH = Path('data') / 'checkpoints'
    _LOGS_PATH = Path('data') / 'logs'

    def __init__(self):
        inputs = Input(shape=Board.encode_shape, name='input')
        hidden = Dense(80, activation='sigmoid', name='hidden_layer_1')(inputs)
        outputs_single = Dense(1, activation='sigmoid', name='output')(hidden)
        self.model = Model(inputs=inputs, outputs=outputs_single)

        self.trace = []
        self.total_moves_played = tf.Variable(
            0, trainable=False, name='total_moves_played', dtype='int64'
        )

        self.writer = tf.summary.create_file_writer(str(self._LOGS_PATH))

        self.loss = tf.Variable(np.inf, trainable=False, name='loss')
        self.games_played = tf.Variable(
            0, trainable=False, name='games_played', dtype='int64'
        )
        self.moves_per_game = tf.Variable(0, trainable=False, name='moves_per_game')
        self.current_move = tf.Variable(0, trainable=False, name='current_move')

        self.total_white_wins = tf.Variable(0, trainable=False, name='total_white_wins')
        self.total_black_wins = tf.Variable(0, trainable=False, name='total_black_wins')

        self.checkpoint = tf.train.Checkpoint(
            global_step=self.total_moves_played,
            model=self.model,
            loss=self.loss,
            games_played=self.games_played,
            moves_per_game=self.moves_per_game,
        )

        self.manager = tf.train.CheckpointManager(
            self.checkpoint, self._CHECKPOINTS_PATH, max_to_keep=3
        )

    def equity(self, board: Board, turn: str):
        state = board.encode(turn)
        output = self.model(state[np.newaxis])
        return output.numpy()[0]

    def reset_episode(self):
        self.trace = []
        self.current_move.assign(0)
        # board = Board()
        # board.reset()
        # self._state = tf.Variable(board.encode(color_move))
        # self._value = tf.Variable(self.model(self._state[np.newaxis]))

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
                step=self.games_played,
            )
            tf.summary.scalar(
                'tests/equity_white_to_win',
                white_to_win_equity[0],
                step=self.games_played,
            )
            tf.summary.scalar(
                'tests/equity_white_to_mars',
                white_to_mars_equity[0],
                step=self.games_played,
            )
            tf.summary.scalar(
                'tests/equity black_to_win',
                black_to_win_equity[0],
                step=self.games_played,
            )
            tf.summary.scalar(
                'tests/equity_black_to_mars',
                black_to_mars_equity[0],
                step=self.games_played,
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
            tf.summary.scalar(
                'tests/random_win_ratio', win_ratio, step=self.games_played
            )
            tf.summary.scalar(
                'tests/random_score_ratio', score_ratio, step=self.games_played
            )
            self.writer.flush()

    def test_against_heuristics(self, num_games=10):
        bot = HeuristicsBot(Colors.WHITE)
        win_ratio, score_ratio = self.test_against_bot(bot, num_games)
        with self.writer.as_default():
            tf.summary.scalar(
                'tests/heuristics_win_ratio', win_ratio, step=self.games_played
            )
            tf.summary.scalar(
                'tests/heuristics_score_ratio', score_ratio, step=self.games_played
            )
            self.writer.flush()

    def find_move(self, color: str, board: Board, dice_roll: tuple[int, int]):
        """
        move is selected based on 1 ply depth
        # TODO: try 2 or 3 ply, prefilter moves after 1st
        """
        start = time.time()

        moves = find_complete_legal_moves(board, color, dice_roll)

        end_complete_moves = time.time()

        max_move = None
        max_prob = -np.inf

        def _get_prob(out):
            if color == Colors.WHITE:
                return out[0]
            else:
                return 1 - out[0]

        for move in moves:

            afterstate = board.copy_board()
            for sm in move:
                afterstate.do_single_move(sm)

            state = afterstate.encode(Colors.opponent(color))
            output = self.model(state[np.newaxis])

            prob = _get_prob(output)

            if prob > max_prob:
                max_prob = prob
                max_move = move

        end_find_move = time.time()

        duration = time.time() - start
        logging.debug(
            f'playing move {max_move} [winning prob = {max_prob}] [time to generate move = {end_complete_moves - start}] '
            f'[time to find best move = {end_find_move - end_complete_moves}] [total time = {duration}]'
        )
        return max_move

    def update(self, color, board, move):
        start = time.time()

        # current state s_t
        state_t = board.encode(color)

        # need to calculate gradient
        with tf.GradientTape() as tape:
            value_t = self.model(state_t[np.newaxis])

        trainable_vars = self.model.trainable_variables
        grads = tape.gradient(value_t, trainable_vars)

        # make move
        afterstate_board = board.copy_board()
        for m in move:
            afterstate_board.do_single_move(m)

        state_t_next = afterstate_board.encode(Colors.opponent(color))
        value_t_next = self.model(state_t_next[np.newaxis])

        def _reward(after_board):
            points = {c: win_condition(after_board, c) for c in Colors.colors}

            # ignoring mars for now
            return 1 if points[Colors.WHITE] else 0

        # calculate reward and td_error (according to https://www.bkgm.com/articles/tesauro/tdl.html)
        if afterstate_board.is_over:
            reward = _reward(afterstate_board)
            td_error = reward - value_t
        else:
            td_error = value_t_next - value_t

        # grad with trace = alpha * td_error * e
        # the total weight change is given by the sum of the
        # weight changes due to each individual output unit
        # according to https://www.csd.uwo.ca/~xling/cs346a/extra/tdgammon.pdf
        td_error = tf.reduce_sum(td_error)

        # initial value for e-> is 0 (according to http://www.incompleteideas.net/book/ebook/node108.html#TD-Gammon)
        if len(self.trace) == 0:
            for grad in grads:
                self.trace.append(
                    tf.Variable(tf.zeros(grad.get_shape()), trainable=False)
                )

        with self.writer.as_default():
            for i in range(len(grads)):
                var_name = self.model.trainable_variables[i].name

                # e-> = lambda * e-> + <grad of output w.r.t weights>
                self.trace[i].assign((self._LAMBDA * self.trace[i]) + grads[i])

                grad_trace = self._ALPHA * td_error * self.trace[i]

                tf.summary.histogram(
                    var_name + '/traces', self.trace[i], step=self.total_moves_played
                )
                tf.summary.histogram(
                    var_name,
                    self.model.trainable_variables[i],
                    step=self.total_moves_played,
                )
                tf.summary.histogram(
                    var_name + '/gradients', grads[i], step=self.total_moves_played
                )
                tf.summary.histogram(
                    var_name + '/grad_traces',
                    grad_trace,
                    step=self.total_moves_played,
                )

                self.model.trainable_variables[i].assign_add(grad_trace)

            duration = time.time() - start
            logging.debug(f'updating model [player = {color}] [duration = {duration}s]')

            tf.summary.scalar(
                'game_stats/total_moves_played',
                self.total_moves_played,
                step=self.total_moves_played,
            )
            tf.summary.scalar(
                'update_step_duration', duration, step=self.total_moves_played
            )

            # values
            for i, v in enumerate(value_t.numpy()[0]):
                tf.summary.scalar(
                    f'train/value/value_{i}', v, step=self.total_moves_played
                )

            for i, v in enumerate(value_t_next.numpy()[0]):
                tf.summary.scalar(
                    f'train/value_next/value_next_{i}', v, step=self.total_moves_played
                )

            td_error_mean = tf.reduce_mean(td_error, name='td_error_mean')
            tf.summary.scalar(
                'train/td_error_mean', td_error_mean, step=self.total_moves_played
            )

            # mean squared error of the difference between the next state and the current state
            self.loss.assign(tf.reduce_mean(tf.square(value_t_next - value_t)))
            tf.summary.scalar('train/loss', self.loss, step=self.total_moves_played)
            tf.summary.scalar(
                'game_stats/current_move',
                self.current_move,
                step=self.total_moves_played,
            )

            if win_condition(afterstate_board, Colors.WHITE):
                self.total_white_wins.assign_add(1)
            elif win_condition(afterstate_board, Colors.BLACK):
                self.total_black_wins.assign_add(1)

            tf.summary.scalar(
                'game_stats/total_white_wins',
                self.total_white_wins,
                step=self.total_moves_played,
            )
            tf.summary.scalar(
                'game_stats/total_black_wins',
                self.total_black_wins,
                step=self.total_moves_played,
            )

            self.writer.flush()

    def train(self, episodes=100, restore=True):
        if restore:
            self.restore()

        test_every_n_moves = 100

        dice = Dice()
        board = Board()

        print()
        print(f'Starting training cycle for {episodes} episodes')

        move_time = []

        pbar = tqdm(range(episodes))
        for i in pbar:

            if i % test_every_n_moves == 0:
                self.test_equity()
                self.test_against_random()
                self.test_against_heuristics()

            board.reset()
            self.reset_episode()

            # randomly select who starts
            starting_color = random.choice([Colors.WHITE, Colors.BLACK])

            last_color = Colors.opponent(starting_color)

            while win_condition(board, last_color) is None:
                start_time = time.time()
                color_to_move = Colors.opponent(last_color)
                dice_roll = dice.throw()

                player_move = self.find_move(color_to_move, board, dice_roll)

                if player_move is not None:
                    self.update(color_to_move, board, player_move)

                    # make move
                    for m in player_move:
                        board.do_single_move(m)

                self.current_move.assign_add(1)
                self.total_moves_played.assign_add(1)

                last_color = color_to_move

                move_time.append(time.time() - start_time)
                avg_time_per_move = np.mean(move_time)
                max_time_per_move = max(move_time)

                pbar.set_postfix(
                    {
                        'games': self.games_played.numpy(),
                        'moves': self.total_moves_played.numpy(),
                        'cur_moves': self.current_move.numpy(),
                        'avg_t': avg_time_per_move,
                        'max_t': max_time_per_move,
                        'loss': self.loss.numpy(),
                        'white': tf.reduce_sum(self.total_white_wins).numpy(),
                        'black': tf.reduce_sum(self.total_black_wins).numpy(),
                    }
                )

            self.games_played.assign_add(1)
            moves_p_game = self.total_moves_played.numpy() / self.games_played.numpy()
            self.moves_per_game.assign(moves_p_game)

            with self.writer.as_default():
                tf.summary.scalar(
                    'game_stats/games_played',
                    self.games_played,
                    step=self.total_moves_played,
                )
                tf.summary.scalar(
                    'game_stats/moves_per_game',
                    self.moves_per_game,
                    step=self.total_moves_played,
                )
                self.writer.flush()

            self.backup()

    def backup(self):
        self.manager.save()

    def restore(self):
        self.checkpoint.restore(self.manager.latest_checkpoint)
        if self.manager.latest_checkpoint:
            print(f'Restored from {self.manager.latest_checkpoint}')
        else:
            print('Initializing from scratch.')


class TDBot:
    """
    This bot uses TD model to play
    """

    def __init__(self, color: str):
        model = TDNardiModel()
        model.restore()
        self._model = model
        self._color = color

    def find_a_move(self, board, dice_roll) -> list[SingleMove]:
        return self._model.find_move(self._color, board, dice_roll)
