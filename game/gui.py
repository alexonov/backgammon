import os
import re
from typing import NamedTuple

from game.components import Board
from game.components import Colors
from game.components import SingleMove


def pad_number(n, length=2):
    """
    pads number with zeros to have at least length of <length>
    """
    n_string = str(n)
    padding_length = max(length - len(n_string), 0)
    return '0' * padding_length + n_string


class CompleteMove(NamedTuple):
    color: str
    dice_roll: tuple[int, int]
    moves: list[SingleMove]

    def __repr__(self):
        prefix = f'{self.color}{self.dice_roll}: '
        if len(self.moves) != 0:
            points = ', '.join(f'{m.position_from}/{m.position_to}' for m in self.moves)
        else:
            points = '-'
        return prefix + points

    @classmethod
    def generate_from_str(cls, move_string):
        regex = re.compile(
            '^([BW])\(([1-6], [1-6])\): '
            '(?:(\d{1,2}\/\d{1,2})[, ]*)?'
            '(?:(\d{1,2}\/\d{1,2})[, ]*)?'
            '(?:(\d{1,2}\/\d{1,2})[, ]*)?'
            '(?:(\d{1,2}\/\d{1,2})[, ]*)?'
            '([-])?$'
        )
        m = regex.match(move_string)
        groups = m.groups()
        color, dice_roll = groups[:2]
        single_moves = (sm for sm in groups[2:] if sm is not None)

        dice_roll = tuple(int(r) for r in dice_roll.split(', '))

        moves = []
        if single_moves != '-':
            for sm in single_moves:
                position_from, position_to = sm.split('/')
                sm_compiled = SingleMove(color, int(position_from), int(position_to))
                moves.append(sm_compiled)

        return cls(color, dice_roll, moves)


class TerminalGUI:
    WHITE_CHECKER_SYMBOL = 'O'
    BLACK_CHECKER_SYMBOL = 'X'
    VERTICAL_SYMBOL = '│'
    HORIZONTAL_SYMBOL = '─'
    TRIANGLE_SYMBOL = '.'
    UPSIDE_DOWN_TRIANGLE_SYMBOL = '˙'
    LEFT_UPPER_CORNER_SYMBOL = '┌'
    RIGHT_UPPER_CORNER_SYMBOL = '┐'
    LEFT_LOWER_CORNER_SYMBOL = '└'
    RIGHT_LOWER_CORNER_SYMBOL = '┘'
    CROSS_SYMBOL = '┼'

    BOARD_HEIGHT = 20

    UPPER_LEFT_POINTS = list(range(12, 6, -1))
    UPPER_RIGHT_POINTS = list(range(6, 0, -1))
    LOWER_LEFT_POINTS = list(range(13, 19, 1))
    LOWER_RIGHT_POINTS = list(range(19, 25, 1))

    def __init__(self):
        pass

    def show_board(self, board: Board, moves=None):
        upper_numbers = '  ' + ' '.join(pad_number(n) for n in self.UPPER_LEFT_POINTS)
        upper_numbers += f' {self.VERTICAL_SYMBOL} '
        upper_numbers += ' '.join(pad_number(n) for n in self.UPPER_RIGHT_POINTS)

        width = len(upper_numbers)
        upper_horizontal_border = ''.join(
            [
                self.LEFT_UPPER_CORNER_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.CROSS_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.RIGHT_UPPER_CORNER_SYMBOL,
            ]
        )
        lower_horizontal_border = ''.join(
            [
                self.LEFT_LOWER_CORNER_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.CROSS_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.RIGHT_LOWER_CORNER_SYMBOL,
            ]
        )

        board_rows = []

        for r_num in range(self.BOARD_HEIGHT):
            if r_num == 0:
                blank_symbol = self.UPSIDE_DOWN_TRIANGLE_SYMBOL
            elif r_num == self.BOARD_HEIGHT - 1:
                blank_symbol = self.TRIANGLE_SYMBOL
            else:
                blank_symbol = ' '

            def _realize_obj(obj):
                try:
                    if obj.color == Colors.WHITE:
                        obj = self.WHITE_CHECKER_SYMBOL
                    else:
                        obj = self.BLACK_CHECKER_SYMBOL
                except AttributeError:
                    obj = blank_symbol

                return obj

            def _build_board(side):
                if side == 'left':
                    upper_points = self.UPPER_LEFT_POINTS
                    lower_points = self.LOWER_LEFT_POINTS
                elif side == 'right':
                    upper_points = self.UPPER_RIGHT_POINTS
                    lower_points = self.LOWER_RIGHT_POINTS
                else:
                    raise ValueError

                # go through slots and extract their content fro the current row
                objects = []
                for i, _ in enumerate(upper_points):
                    obj = None
                    try:
                        upper_num = upper_points[i]
                        slot_ind = upper_num - 1
                        checker_ind = r_num
                        obj = board.slots[slot_ind].checkers[checker_ind]
                    except IndexError:
                        ...
                    try:
                        lower_num = lower_points[i]
                        slot_ind = lower_num - 1
                        checker_ind = self.BOARD_HEIGHT - r_num - 1
                        obj = board.slots[slot_ind].checkers[checker_ind]
                    except IndexError:
                        ...

                    objects.append(_realize_obj(obj))

                board_row = ' '.join(' ' + o for o in objects) + '  '
                return board_row

            left_board = _build_board('left')
            right_board = _build_board('right')

            row = (
                self.VERTICAL_SYMBOL
                + left_board
                + self.VERTICAL_SYMBOL
                + right_board
                + self.VERTICAL_SYMBOL
            )
            board_rows.append(row)

        lower_numbers = '  ' + ' '.join(pad_number(n) for n in self.LOWER_LEFT_POINTS)
        lower_numbers += f' {self.VERTICAL_SYMBOL} '
        lower_numbers += ' '.join(pad_number(n) for n in self.LOWER_RIGHT_POINTS)

        # show moves if present
        if moves:
            # pair moves
            formatted_moves = [str(m) for m in moves]
            formatted_moves_paired = [
                '; '.join(formatted_moves[i : i + 2])
                for i in range(0, len(formatted_moves), 2)
            ]
            move_max_with = max(len(m) for m in formatted_moves_paired)

            # split into columns of height = board height
            move_lines = [''] * self.BOARD_HEIGHT
            for i, m in enumerate(formatted_moves_paired):
                ind = i % self.BOARD_HEIGHT
                move_lines[ind] = (
                    ' ' * 3
                    + (f'{i}. ' + m).ljust(move_max_with + 5)
                    + self.VERTICAL_SYMBOL
                )

            # add blank line for readability
            if len(formatted_moves_paired) > self.BOARD_HEIGHT:
                move_lines[len(formatted_moves_paired) % self.BOARD_HEIGHT] = (
                    ' ' * 3 + ''.ljust(move_max_with + 5) + self.VERTICAL_SYMBOL
                )

            board_rows = [b + l for b, l in zip(board_rows, move_lines)]

        board_string = '\n'.join(
            [
                upper_numbers,
                upper_horizontal_border,
                *board_rows,
                lower_horizontal_border,
                lower_numbers,
            ]
        )

        os.system('clear')
        print(board_string)
