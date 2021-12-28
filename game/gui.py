from .components import Board, Colors
import os


def pad_number(n, length=2):
    """
    pads number with zeros to have at least length of <length>
    """
    n_string = str(n)
    padding_length = max(length - len(n_string), 0)
    return '0' * padding_length + n_string


class TerminalGUI:
    WHITE_CHECKER_SYMBOL = '☻'
    BLACK_CHECKER_SYMBOL = '☺'
    VERTICAL_SYMBOL = '│'
    HORIZONTAL_SYMBOL = '─'
    TRIANGLE_SYMBOL = 'Λ'
    UPSIDE_DOWN_TRIANGLE_SYMBOL = 'V'
    LEFT_UPPER_CORNER_SYMBOL = '┌'
    RIGHT_UPPER_CORNER_SYMBOL = '┐'
    LEFT_LOWER_CORNER_SYMBOL = '└'
    RIGHT_LOWER_CORNER_SYMBOL = '┘'
    CROSS_SYMBOL = '┼'

    BOARD_HEIGHT = 20

    UPPER_LEFT_POINTS = list(range(12, 6, -1))
    UPPER_RIGHT_POINTS = list(range(6, 0, -1))
    LOWER_LEFT_POINTS = list(range(13, 18, 1))
    LOWER_RIGHT_POINTS = list(range(18, 25, 1))

    def __init__(self):
        pass

    def show_board(self, board: Board):
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
                self.RIGHT_UPPER_CORNER_SYMBOL
            ]
        )
        lower_horizontal_border = ''.join(
            [
                self.LEFT_LOWER_CORNER_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.CROSS_SYMBOL,
                self.HORIZONTAL_SYMBOL * (width // 2),
                self.RIGHT_LOWER_CORNER_SYMBOL
            ]
        )

        board_rows = []
        half_inner_width = len(upper_numbers[:width // 2].strip())

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

            row = self.VERTICAL_SYMBOL + left_board + self.VERTICAL_SYMBOL + right_board + self.VERTICAL_SYMBOL
            board_rows.append(row)

        lower_numbers = '  ' + ' '.join(pad_number(n) for n in self.LOWER_LEFT_POINTS)
        lower_numbers += f' {self.VERTICAL_SYMBOL} '
        lower_numbers += ' '.join(pad_number(n) for n in self.LOWER_RIGHT_POINTS)

        board_string = '\n'.join([
            upper_numbers,
            upper_horizontal_border,
            *board_rows,
            lower_horizontal_border,
            lower_numbers
        ])

        os.system('clear')
        print(board_string)
