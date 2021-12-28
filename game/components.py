"""
classes to represent the board of the game

board positions go from 1 to 24 to conform to standard backgammon notation
"""
from typing import NamedTuple
from random import randrange


MIN_POSITION = 0
MAX_POSITION = 23


def convert_coordinates(position: int) -> int:
    assert MIN_POSITION <= position
    lookup = list(range(12, 24)) + list(range(12))
    return lookup[position]


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


class PlacementNotPossibleError(Exception):
    pass


class Checker:
    def __init__(self, color: str, position: int):
        assert MIN_POSITION <= position <= MAX_POSITION, 'Position is out of range'
        self.color = color
        self.point = position

    def __repr__(self):
        return f'{self.color} checker at {self.point}'


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
        or a slop taken by the same color checker
        """
        return self.color is None or self.color == checker.color

    def place_checker(self, checker: Checker):
        if self.can_place_checker(checker):
            self.checkers.append(checker)
        else:
            raise PlacementNotPossibleError(
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
        self.slot_lookup = {
            Colors.WHITE: [i for i in sorted_inds(self.slots, key_func=lambda x: x.position[Colors.WHITE])],
            Colors.BLACK: [i for i in sorted_inds(self.slots, key_func=lambda x: x.position[Colors.BLACK])]
        }
        self.moves = []
        self.checkers = {
            Colors.WHITE: [],
            Colors.BLACK: [],
        }

    def get_slot(self, color: str, position: int):
        ind = self.slot_lookup[color][position]
        return self.slots[ind]

    def reset(self):
        """
        resets the board for a new game
        """
        self.checkers = {
            Colors.WHITE: [Checker(Colors.WHITE, MIN_POSITION) for _ in range(15)],
            Colors.BLACK: [Checker(Colors.BLACK, MIN_POSITION) for _ in range(15)],
        }

        for _, checkers in self.checkers.items():
            for c in checkers:
                self.get_slot(c.color, c.point).checkers.append(c)

        self.moves = []

    def _dummy_setup(self, num=1):
        for s in self.slots:
            if s.real_position % 2 == 0:
                color = Colors.WHITE
            else:
                color = Colors.BLACK
            s.checkers = [Checker(color, s.position[color]) for _ in range(num)]

    def is_single_move_obstructed(self, color: str, single_move: SingleMove):
        """
        checks if move is not obstructed by enemy's checkers
        """
        slots = self.slot_lookup[color]
        try:
            # check if there's a checker
            assert not slots[
                single_move.position_from].is_empty, f'No checker to move in {single_move.position_from}'

            # if not bearing off, check that there's no opponent's checker
            if single_move.position_to <= MAX_POSITION:
                checker_to_move = slots[single_move.position_to].checkers[-1]
                assert slots[single_move.position_to].can_place_checker(
                    checker_to_move), f'Cannot place checker from {single_move.position_from} to {single_move.position_to}'
        except AssertionError:
            return False
        else:
            return True

    def is_single_move_legal(self, move: SingleMove):
        """
        checks if move can be legally made
        1. not obstructed
        2. moves in the right direction
        3. not blocking opponent's bear-off completely (unless there's checker at home)
        4. bearing off only allowed if all are ot home
        """
        assert MIN_POSITION < move.position_from, f'position_from is out of range, must be at least {MIN_POSITION}'
        assert MIN_POSITION < move.position_to, f'position_to is out of range, must be at least {MIN_POSITION}'
        pass

    def is_move_legal(self, move: Move):
        """
        1. only one take from the head
        2. if bering off overshooting allowed only if there is no other not-bearing-off move
        """

    def do_move(self, move: Move):
        """
        move checkers according to move variable
        """
        self.slot_lookup[move.color]
