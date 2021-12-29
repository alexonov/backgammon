"""
classes to represent the board of the game

board positions go from 1 to 24 to conform to standard backgammon notation
"""
from typing import NamedTuple
from random import randrange


MIN_POSITION = 1
MAX_POSITION = 24


def norm_index(position):
    """
    convert board point position (from MIN to MAX) to
    absolute normalized position from 0 to 23
    """
    return list(range(MIN_POSITION, MAX_POSITION + 1)).index(position)


def convert_coordinates(position: int) -> int:
    assert MIN_POSITION <= position
    mid_point = MAX_POSITION - 12
    lookup = list(range(mid_point + 1, MAX_POSITION + 1)) + list(range(MIN_POSITION, mid_point + 1))
    lookup_ind = norm_index(position)
    return lookup[lookup_ind]


def sorted_inds(l: list, key_func):
    return sorted(range(len(l)), key=lambda k: key_func(l[k]))


class Colors:
    WHITE = 'white'
    BLACK = 'black'

    @classmethod
    def opponent(cls, color: str):
        if color == cls.BLACK:
            return cls.WHITE
        elif color == cls.WHITE:
            return cls.BLACK
        else:
            raise ValueError


class Dice:
    def __init__(self, max_point=6):
        self.max_point = max_point

    def throw(self):
        return randrange(self.max_point + 1), randrange(self.max_point + 1)


class SingleMove(NamedTuple):
    position_from: int
    position_to: int


class Move(NamedTuple):
    color: str
    first_move: SingleMove
    second_move: SingleMove

    def __repr__(self):
        return f'{self.color}: {self.first_move.position_from}->{self.first_move.position_to}, {self.second_move.position_from}->{self.second_move.position_to}'


class MoveNotPossibleError(Exception):
    pass


class Checker(NamedTuple):
    color: str

    def __repr__(self):
        return f'{self.color} checker'


class Slot:
    def __init__(self, real_position: int):
        assert MIN_POSITION <= real_position <= MAX_POSITION, 'Position is out of range'
        self.checkers: list[Checker] = []
        self.real_position = real_position
        self.position = {
            Colors.WHITE: real_position,
            Colors.BLACK: convert_coordinates(real_position)
        }

    @property
    def is_empty(self):
        return len(self.checkers) == 0

    @property
    def color(self):
        if self.is_empty:
            return None
        else:
            return self.checkers[-1].color

    def can_place_checker(self, checker: Checker):
        """
        checker can only be placed on an empty slot
        or a slot taken by the same color checker
        """
        return self.is_empty or self.color == checker.color

    def place_checker(self, checker: Checker):
        if self.can_place_checker(checker):
            self.checkers.append(checker)
        else:
            raise MoveNotPossibleError(
                f'Cannot place checker of color {checker.color} into the slot {self.position[checker.color]}')

    def __repr__(self):
        repr = f'Slot {self.real_position}: '
        if self.is_empty:
            return repr + 'empty'
        else:
            return repr + f'{len(self.checkers)} {self.color} checkers'


class Board:
    def __init__(self):
        self.slots = [Slot(i) for i in range(MIN_POSITION, MAX_POSITION + 1)]
        self.slot_lookup_dict = {
            Colors.WHITE: [i for i in sorted_inds(self.slots, key_func=lambda x: x.position[Colors.WHITE])],
            Colors.BLACK: [i for i in sorted_inds(self.slots, key_func=lambda x: x.position[Colors.BLACK])]
        }
        self.moves = []

    def get_slot(self, color: str, position: int):
        try:
            norm_position = norm_index(position)
            ind = self.slot_lookup_dict[color][norm_position]
            return self.slots[ind]
        except IndexError:
            return None

    def reset(self):
        """
        resets the board for a new game
        """
        for _ in range(15):
            self.get_slot(Colors.WHITE, MIN_POSITION).place_checker(Checker(Colors.WHITE))
            self.get_slot(Colors.BLACK, MIN_POSITION).place_checker(Checker(Colors.BLACK))

        self.moves = []

    def _dummy_setup(self, num=1):
        for s in self.slots:
            if s.real_position % 2 == 0:
                color = Colors.WHITE
            else:
                color = Colors.BLACK
            s.checkers = [Checker(color) for _ in range(num)]

    def is_single_move_possible(self, color: str, single_move: SingleMove):
        """
        checks if move is not obstructed by enemy's checkers
        """

        slot_from = self.get_slot(color, single_move.position_from)
        slot_to = self.get_slot(color, single_move.position_from)
        try:
            # check if there's a checker
            assert not slot_from.is_empty, f'No checker to move in {single_move.position_from}'

            # if not bearing off, check that there's no opponent's checker
            if slot_to is not None:
                checker_to_move = slot_from.checkers[-1]
                assert slot_to.can_place_checker(
                    checker_to_move), f'Cannot place checker from {single_move.position_from} to {single_move.position_to}'
        except AssertionError:
            return False
        else:
            return True

    def do_move(self, move: Move):
        """
        move checkers according to move variable
        """
        if self.is_single_move_possible(move.color, move.first_move):
            self.do_single_move(move.color, move.first_move)
            if self.is_single_move_possible(move.color, move.second_move):
                self.do_single_move(move.color, move.second_move)
                self.moves.append(move)
            else:
                self.undo_single_move(move.color, move.first_move)
        else:
            raise MoveNotPossibleError(f'Can not make move {move}')

    def do_single_move(self, color, single_move):
        checker = self.get_slot(color, single_move.position_from).checkers.pop()
        self.get_slot(color, single_move.position_to).place_checker(checker)

    def undo_single_move(self, color, single_move):
        pos_from = single_move.position_to
        pos_to = single_move.position_from
        self.do_single_move(color, SingleMove(pos_from, pos_to))
