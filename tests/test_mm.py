#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
import pytest
from garleek.mm.tinker import _parse_tinker_testgrad, _parse_tinker_analyze, _parse_tinker_testhess


def test_prepare_tinker_xyz():
    pass


def test_prepare_tinker_inpkey():
    pass


@pytest.mark.parametrize("path, energy, dipole", [
    ["moredata/parsers/tinker_analyze.out", -2.6773, [0, 0, 0]]
])
def test__parse_tinker_analyze(path, energy, dipole):
    with open(path) as f:
        parsed_energy, parsed_dipole = _parse_tinker_analyze(f.read())
        assert energy == parsed_energy
        assert (parsed_dipole == dipole).all()


@pytest.mark.parametrize("path, last_value", [
    ["moredata/parsers/tinker_testgrad.out", -3.3071]
])
def test__parse_tinker_testgrad(path, last_value):
    with open(path) as f:
        data = _parse_tinker_testgrad(f.read())
        assert data[-1][-1] == last_value


@pytest.mark.parametrize("path, natoms, last_diagonal, last_off_diagonal", [
    ["moredata/parsers/tinker_testhess.out", 11, 85.5836, -0.4860]
])
def test__parse_tinker_testhess(path, natoms, last_diagonal, last_off_diagonal):
    data = _parse_tinker_testhess(path, natoms)
    print(data)
    assert data[-1][-1] == last_diagonal
    assert data[-1][-2] == last_off_diagonal


def test_run_tinker():
    pass

