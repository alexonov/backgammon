"""
classes to represent the board of the game

board positions go from 1 to 24 to conform to standard backgammon notation
"""
from enum import Enum, auto


class Color(Enum):
    WHITE = auto()
    BLACK = auto()


class PlacementNotPossibleError(Exception):
    pass


class Checker:
    def __init__(self, color: Enum, point: int):
        assert 0 < point < 25, 'Position is out of range'
        self.color = color
        self.point = point


class Slot:
    def __init__(self, point: int):
        assert 0 < point < 25, 'Position is out of range'
        self.checkers: list[Checker] = []
        self.point = point

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
            raise PlacementNotPossibleError(f'Cannot place checker of color {checker.color} into the slot {self.point}')


class Board:
    def __init__(self):
        self.slots = [Slot(i) for i in range(1, 25)]
        self.white_checkers = []
        self.black_checkers = []

    def reset(self):
        """
        resets the board for a new game
        """
        self.black_checkers = [Checker(Color.BLACK, 12) for _ in range(15)]
        self.white_checkers = [Checker(Color.WHITE, 24) for _ in range(15)]

    @property
    def checkers(self):
        return self.black_checkers + self.white_checkers

    def move(self, point_from: int, point_to: int):
        assert 0 < point_from < 25, 'point_from is out of range'
        assert 0 < point_to < 25, 'point_to is out of range'

