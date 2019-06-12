import pytest

from hnccorr.seeder import LocalCorrelationSeeder


def test_local_corr_seeder(MM):
    LCS = LocalCorrelationSeeder(neighborhood_size=3, keep_fraction=0.2)
    LCS.select_seeds(MM)
    assert LCS.next() == (9,)
    assert LCS.next() == (8,)
    assert LCS.next() is None


def test_local_corr_seeder_reset(MM):
    LCS = LocalCorrelationSeeder(neighborhood_size=3, keep_fraction=0.2)
    LCS.select_seeds(MM)
    assert LCS.next() == (9,)

    LCS.reset()
    assert LCS.next() == (9,)


def test_seeder_exclude_pixels(MM):
    LCS = LocalCorrelationSeeder(neighborhood_size=3, keep_fraction=0.2)
    LCS.select_seeds(MM)
    assert LCS.next() == (9,)
    LCS.exclude_pixels({(8,)})
    assert LCS.next() is None


def test_seeder_exclude_pixels_boundary(MM):
    LCS = LocalCorrelationSeeder(neighborhood_size=3, keep_fraction=0.2, padding=2)
    LCS.select_seeds(MM)
    assert LCS.next() == (9,)
    LCS.exclude_pixels({(6,)})
    assert LCS.next() is None
