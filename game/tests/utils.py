import itertools


def assert_no_duplicated_moves(moves):
    duplicates_removed = list(moves for moves, _ in itertools.groupby(moves))
    assert len(duplicates_removed) == len(moves)
