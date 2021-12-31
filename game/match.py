"""
used to setup and play the game
"""
import random
import re
import time

from game.bot import Bot
from game.components import Board
from game.components import Colors
from game.components import Dice
from game.components import SingleMove
from game.gui import TerminalGUI
from game.rules import find_complete_legal_moves
from game.rules import opponent
from game.rules import win_condition


def parse_move(moves):
    parsed_moves = []
    for move in moves.split(' '):
        regex = re.compile('^(\d*)->(\d*)$')
        m = regex.match(move)
        position_from, position_to = m.groups()
        parsed_moves.append((int(position_from), int(position_to)))
    return parsed_moves


class Players:
    AI = 'AI'
    HUMAN = 'Human'


class CompleteMove:
    def __init__(self):
        pass


def play_match(white, black, show_gui=True):
    players = {Colors.WHITE: white, Colors.BLACK: black}
    gui = TerminalGUI()
    board = Board()
    dice = Dice()
    bots = {Colors.WHITE: Bot(Colors.WHITE), Colors.BLACK: Bot(Colors.BLACK)}

    moves = []

    def _show_message(message, pause=0.1):
        print()
        print(message)
        time.sleep(pause)

    board.reset()

    # randomly select who starts
    starting_color = random.choice([Colors.WHITE, Colors.BLACK])

    if show_gui:
        gui.show_board(board)
        _show_message(f'{starting_color} starts the game')

    last_color = opponent(starting_color)
    while win_condition(board, last_color) is None:

        if show_gui:
            gui.show_board(board)

        color_to_move = opponent(last_color)

        dice_roll = dice.throw()

        if show_gui:
            _show_message(f'Player {color_to_move} turn.')
            _show_message(f'Throwing dice: {dice_roll}')

        if players[color_to_move] == Players.HUMAN:
            allowed_moves = find_complete_legal_moves(board, color_to_move, dice_roll)

            # ask for a move
            while True:
                input_moves = input(
                    'Make a move (format is from->to space separated): '
                )
                try:
                    parsed_moves = parse_move(input_moves)
                    player_moves = [
                        SingleMove(color_to_move, m[0], m[1]) for m in parsed_moves
                    ]
                    assert player_moves in allowed_moves
                except (AttributeError, AssertionError):
                    print('Not an appropriate move.')
                else:
                    break
        else:
            player_moves = bots[color_to_move].find_a_move(board, dice_roll)

        # make move
        for m in player_moves:
            board.do_single_move(m)

        # save move
        moves.append(player_moves)

        last_color = color_to_move

        if show_gui:
            _ = input('Press ENTER key to continue...')

    if show_gui:
        gui.show_board(board)
        _show_message(
            f'Player {last_color} won with {win_condition(board, last_color)}!'
        )
