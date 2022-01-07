"""
used to setup and play the game
"""
import datetime
import random
import re
from pathlib import Path

from game.components import Board
from game.components import Colors
from game.components import Dice
from game.components import SingleMove
from game.gui import CompleteMove
from game.gui import TerminalGUI
from game.rules import find_complete_legal_moves
from game.rules import win_condition
from game.td_model import TDNardiModel


def parse_moves(moves, splitter=','):
    parsed_moves = []
    for move in moves.split(','):
        position_from, position_to = parse_move(move)
        parsed_moves.append((int(position_from), int(position_to)))
    return parsed_moves


def parse_move(move):
    regex = re.compile('^(\d*) (\d*)$')
    m = regex.match(move)
    position_from, position_to = m.groups()
    return int(position_from), int(position_to)


class Players:
    AI = 'AI'
    HUMAN = 'Human'


def play_match(white=None, black=None, show_gui=False):
    gui = TerminalGUI()
    board = Board()
    dice = Dice()
    bots = {}
    player_name = {}
    player_type = {}

    model = TDNardiModel()
    model.restore()

    # if None - then human
    if white is not None:
        bots[Colors.WHITE] = white
        player_type[Colors.WHITE] = Players.AI
        player_name[Colors.WHITE] = white.__class__.__name__
    else:
        player_type[Colors.WHITE] = Players.HUMAN
        player_name[Colors.WHITE] = Players.HUMAN

    if black is not None:
        bots[Colors.BLACK] = black
        player_type[Colors.BLACK] = Players.AI
        player_name[Colors.BLACK] = black.__class__.__name__
    else:
        player_type[Colors.BLACK] = Players.HUMAN
        player_name[Colors.BLACK] = Players.HUMAN

    moves = []

    def _show_message(message, pause=0.1):
        print()
        print(message)
        # time.sleep(pause)

    def _show_board(turn):
        equity = model.equity(board, turn)
        gui.show_board(board, moves, equity)

    board.reset()

    # randomly select who starts
    starting_color = random.choice([Colors.WHITE, Colors.BLACK])

    if show_gui:
        _show_message(f'{starting_color} starts the game')

    last_color = Colors.opponent(starting_color)
    while win_condition(board, last_color) is None:

        color_to_move = Colors.opponent(last_color)
        dice_roll = dice.throw()

        if show_gui:
            _show_board(color_to_move)
            _show_message(
                f'Player {color_to_move} ({player_name[color_to_move]}) turn.'
            )
            _show_message(f'Throwing dice: {dice_roll}')

        if player_type[color_to_move] == Players.HUMAN:
            allowed_moves = find_complete_legal_moves(
                board, color_to_move, dice_roll, filter_moves=False
            )

            # ask for a move
            num_moves_required = max(len(m) for m in allowed_moves)
            moves_made = []
            while len(moves_made) < num_moves_required:
                num_moves_made = len(moves_made)

                if num_moves_made > 0:
                    print(f'moves made: {moves_made}')

                input_move = input(
                    'Make a move (format is from to (space separated), U to undo previous move): '
                )
                if input_move == 'U':
                    if num_moves_made > 0:
                        board.undo_single_move(moves_made.pop())
                    else:
                        pass
                else:
                    try:
                        parsed_move = parse_move(input_move)
                        player_move = SingleMove(color_to_move, *parsed_move)
                        assert player_move in [m[num_moves_made] for m in allowed_moves]

                        board.do_single_move(player_move)

                        moves_made.append(player_move)

                    except (AttributeError, AssertionError):
                        print('Not an appropriate move.')

                _show_board(color_to_move)
                _show_message(
                    f'Player {color_to_move} ({player_name[color_to_move]}) turn.'
                )
                _show_message(f'Throwing dice: {dice_roll}')

            player_moves = moves_made
        else:
            player_moves = bots[color_to_move].find_a_move(board, dice_roll)
            # make move
            if player_moves:
                for m in player_moves:
                    board.do_single_move(m)

        # save move
        moves.append(CompleteMove(color_to_move, dice_roll, player_moves))

        last_color = color_to_move

        if show_gui:
            _ = input('Press ENTER key to continue...')

    if show_gui:
        _show_board(Colors.opponent(last_color))
        _show_message(
            f'Player {last_color} ({player_name[last_color]}) won with {win_condition(board, last_color)}!'
        )
    return moves, {'winner': last_color, 'score': win_condition(board, last_color)}


def unique_name():
    uniq_filename = (
        str(datetime.datetime.now().date())
        + '_'
        + str(datetime.datetime.now().time()).replace(':', '-').replace('.', '-')
    )
    return uniq_filename


def save_moves(moves: list[CompleteMove], file_name=None):
    HISTORY_FOLDER = 'data/recorded_games'
    file_name = file_name or unique_name()
    with open(Path(HISTORY_FOLDER) / f'{file_name}.txt', 'w') as f:
        f.writelines([str(m) + '\n' for m in moves])
