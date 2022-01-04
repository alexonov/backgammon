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

from game.components import Board
from game.components import Colors
from game.components import Dice
from game.rules import find_complete_legal_moves
from game.rules import opponent
from game.rules import win_condition


class TDNardiModel:
    _LAMBDA = 0.7
    _ALPHA = 0.01

    _CHECKPOINTS_PATH = Path('data') / 'checkpoints'
    _LOGS_PATH = Path('data') / 'logs'

    def __init__(self):
        inputs = Input(shape=Board.ENCODED_SHAPE, name='input')
        hidden_1 = Dense(50, activation='sigmoid', name='hidden_layer_1')(inputs)
        hidden_2 = Dense(20, activation='sigmoid', name='hidden_layer_2')(hidden_1)
        outputs = Dense(4, activation='sigmoid', name='output')(hidden_2)
        self.model = Model(inputs=inputs, outputs=outputs)

        self._trace = []
        self.total_moves_played = tf.Variable(
            0, trainable=False, name='total_moves_played', dtype='int64'
        )

        self.writer = tf.summary.create_file_writer(str(self._LOGS_PATH))

        self.loss = tf.Variable(np.inf, trainable=False, name='loss')
        self.games_played = tf.Variable(0, trainable=False, name='games_played')
        self.moves_per_game = tf.Variable(0, trainable=False, name='moves_per_game')
        self.current_move = tf.Variable(0, trainable=False, name='current_move')

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

    def reset_episode(self):
        self._trace = []
        self.current_move.assign(0)
        # board = Board()
        # board.reset()
        # self._state = tf.Variable(board.encode(color_move))
        # self._value = tf.Variable(self.model(self._state[np.newaxis]))

    def find_move(self, color: str, board: Board, dice_roll: tuple[int, int]):
        """
        move is selected based on 1 ply depth
        # TODO: try 2 or 3 ply, prefilter moves after 1st
        """
        start = time.time()

        moves = find_complete_legal_moves(board, color, dice_roll)

        max_move = None
        max_prob = -np.inf

        def _get_prob(output):
            if color == Colors.WHITE:
                return output[0][0] + output[0][2]
            else:
                return output[0][1] + output[0][3]

        for move in moves:
            afterstate = board.copy_board()
            for m in move:
                afterstate.do_single_move(m)

            state = afterstate.encode(color)
            output = self.model(state[np.newaxis])

            # output has 4 probabilities
            # 0. prob of white winning
            # 1. prob of black winning
            # 2. prob of white winning with mars
            # 3. prob of black winning with mars
            # select the one that gives highest sum

            prob = _get_prob(output)

            if prob > max_prob:
                max_prob = prob
                max_move = move

        duration = time.time() - start
        logging.debug(
            'playing move [player = %d] [move = %s] [winning prob = %f] [duration = %ds]',
            color,
            str(max_move),
            max_prob,
            duration,
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

        state_t_next = afterstate_board.encode(color)
        value_t_next = self.model(state_t_next[np.newaxis])

        def _reward(after_board):
            white_won = win_condition(after_board, Colors.WHITE)
            black_won = win_condition(after_board, Colors.BLACK)
            r = np.zeros((4,))
            if white_won:
                r[white_won - 1] = white_won
            elif black_won:
                r[black_won - 1] = black_won
            return tf.Variable(r[np.newaxis], dtype='float32')

        # calculate reward and td_error (according to https://www.bkgm.com/articles/tesauro/tdl.html)
        if afterstate_board.is_over:
            reward = _reward(afterstate_board)
            td_error = reward - value_t
        else:
            td_error = value_t_next - value_t

        # initial value for e-> is 0 (according to http://www.incompleteideas.net/book/ebook/node108.html#TD-Gammon)
        if len(self._trace) == 0:
            for grad in grads:
                self._trace.append(
                    tf.Variable(tf.zeros(grad.get_shape()), trainable=False)
                )

        with self.writer.as_default():
            for i in range(len(grads)):
                var_name = self.model.trainable_variables[i].name
                tf.summary.histogram(
                    var_name,
                    self.model.trainable_variables[i],
                    step=self.total_moves_played,
                )
                tf.summary.histogram(
                    var_name + '/gradients/grad', grads[i], step=self.total_moves_played
                )

                # e-> = lambda * e-> + <grad of output w.r.t weights>
                self._trace[i].assign((self._LAMBDA * self._trace[i]) + grads[i])
                tf.summary.histogram(
                    var_name + '/traces', self._trace[i], step=self.total_moves_played
                )

                # grad with trace = alpha * td_error * e
                # the total weight change is given by the sum of the
                # weight changes due to each individual output unit
                # according to https://www.csd.uwo.ca/~xling/cs346a/extra/tdgammon.pdf
                grad_trace = sum(
                    self._ALPHA * unit_error * self._trace[i]
                    for unit_error in td_error.numpy()[0]
                )
                tf.summary.histogram(
                    var_name + '/gradients/trace',
                    grad_trace,
                    step=self.total_moves_played,
                )

                self.model.trainable_variables[i].assign_add(grad_trace)

            duration = time.time() - start
            logging.debug(f'updating model [player = {color}] [duration = {duration}s]')

            tf.summary.scalar(
                'total_moves_played',
                self.total_moves_played,
                step=self.total_moves_played,
            )
            tf.summary.scalar('duration', duration, step=self.total_moves_played)

            # values
            for i, v in enumerate(value_t.numpy()[0]):
                tf.summary.scalar(f'value/value_{i}', v, step=self.total_moves_played)

            for i, v in enumerate(value_t_next.numpy()[0]):
                tf.summary.scalar(
                    f'value_next/value_next_{i}', v, step=self.total_moves_played
                )

            td_error_mean = tf.reduce_mean(td_error, name='td_error_mean')
            tf.summary.scalar(
                'td_error_mean', td_error_mean, step=self.total_moves_played
            )

            # mean squared error of the difference between the next state and the current state
            self.loss.assign(tf.reduce_mean(tf.square(value_t_next - value_t)))
            tf.summary.scalar('loss', self.loss, step=self.total_moves_played)
            tf.summary.scalar(
                'current_move', self.current_move, step=self.total_moves_played
            )
            tf.summary.scalar(
                'games_played', self.games_played, step=self.total_moves_played
            )
            tf.summary.scalar(
                'moves_per_game', self.moves_per_game, step=self.total_moves_played
            )

            self.writer.flush()

    def train(self, episodes=100, restore=True):
        if restore:
            self.restore()

        dice = Dice()
        board = Board()

        print()
        print(f'Starting training cycle for {episodes} episodes')

        move_time = []

        pbar = tqdm(range(episodes))
        for _ in pbar:
            board.reset()
            self.reset_episode()

            # randomly select who starts
            starting_color = random.choice([Colors.WHITE, Colors.BLACK])

            last_color = opponent(starting_color)

            while win_condition(board, last_color) is None:
                start_time = time.time()
                color_to_move = opponent(last_color)
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
                        'avg_t_move': avg_time_per_move,
                        'max_t_move': max_time_per_move,
                        'loss': self.loss.numpy(),
                    }
                )

            self.games_played.assign_add(1)
            moves_p_game = self.total_moves_played.numpy() / self.games_played.numpy()
            self.moves_per_game.assign(moves_p_game)

            self.backup()

    def backup(self):
        self.manager.save()

    def restore(self):
        self.checkpoint.restore(self.manager.latest_checkpoint)
        if self.manager.latest_checkpoint:
            print(f'Restored from {self.manager.latest_checkpoint}')
        else:
            print('Initializing from scratch.')
