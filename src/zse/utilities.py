"""
This module contains general utilities
to be used by other functions in ZSE.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from ase.geometry import get_distances
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.io.ase import AseAtomsAdaptor

from zse.collections.framework import get_framework
from zse.collections.framework import get_osites as get_osites_
from zse.collections.framework import get_tsites as get_tsites_

if TYPE_CHECKING:
    pass


def center(atoms, index):
    """
    This function will center an atoms object around an index.
    """
    com = atoms.get_center_of_mass()
    trans = com - atoms[index].position
    atoms.translate(trans)
    atoms.wrap()
    return atoms, trans


def get_osites(code: str):
    z = get_framework(code)
    osites, omult = get_osites_(code)
    oinds = [atom.index for atom in z if atom.symbol == "O"]
    index = 0
    first_os = []
    for m in omult:
        first_os.append(oinds[index])
        index += m
    return osites, omult, first_os


def get_tsites(code, T_atoms: list[str] = None):
    if not T_atoms:
        T_atoms = ["Si", "Al"]
    z = get_framework(code)
    tsites, tmult = get_tsites_(code)
    tinds = [atom.index for atom in z if atom.symbol in T_atoms]
    index = 0
    first_ts = []
    for m in tmult:
        first_ts.append(tinds[index])
        index += m
    return tsites, tmult, first_ts


def label_osites(atoms, code):
    z = get_framework(code)
    osites, omult, _ = get_osites(code)

    zcell = z.cell.cellpar()[:3]
    acell = atoms.cell.cellpar()[:3]
    repeat = [int(round(ac / zc)) for zc, ac in zip(zcell, acell)]
    z = z.repeat(repeat)
    oinds = [atom.index for atom in z if atom.symbol == "O"]

    rp = np.prod(repeat)
    Dict = {}
    j = 0
    for _ in range(rp):
        for s, t in enumerate(osites):
            for _ in range(omult[s]):
                Dict[oinds[j]] = t
                j += 1

    return Dict


def label_tsites(atoms, code):
    z = get_framework(code)
    tsites, tmult, _ = get_tsites(code)
    tinds = [atom.index for atom in z if atom.symbol != "O"]

    zcell = z.cell.cellpar()[:3]
    acell = atoms.cell.cellpar()[:3]
    repeat = [int(round(ac / zc)) for zc, ac in zip(zcell, acell)]
    z = z.repeat(repeat)
    tinds = [atom.index for atom in z if atom.symbol != "O"]

    rp = np.prod(repeat)
    Dict = {}
    j = 0
    for _ in range(rp):
        for s, t in enumerate(tsites):
            for _ in range(tmult[s]):
                Dict[tinds[j]] = t
                j += 1

    return Dict


def scale_cell(atoms):
    diff = 1
    sil = 3.1
    mult = 1
    si = [atom.index for atom in atoms if atom.symbol == "Si"]
    zsi = atoms[si]
    while diff > 0.01:
        cell = atoms.cell.cellpar()
        for i in range(3):
            cell[i] = cell[i] * mult
        zsi.set_cell(cell, scale_atoms=True)
        ncell = zsi.get_cell()
        positions = zsi.get_positions()
        distances = get_distances(positions, cell=ncell, pbc=[1, 1, 1])[1]
        temp = []
        for line in distances:
            masked_line = np.ma.masked_equal(line, 0.0, copy=False)
            temp.append(masked_line.min())
        silm = np.average(temp)
        diff = abs(silm - sil)
        mult = sil / silm
    atoms.set_cell(cell, scale_atoms=True)

    return atoms


def site_labels(atoms, code):
    """
    This function will get the atom site labels (as defined by the IZA) for
    your atoms object. Be sure to remove any adsorbates from your zeolite
    framework before using this function or else it won't work. This function
    will work with T sites that have been exchanged for Al (or any atom).

    atoms: atoms object containing a zeolite you want labels for

    code: the zeolite framework code of your atoms object (i.e. 'CHA')
    """

    tdict = label_tsites(atoms, code)
    odict = label_osites(atoms, code)
    all_labels = {**tdict, **odict}

    z = get_framework(code)
    zcell = z.cell.cellpar()[:3]
    acell = atoms.cell.cellpar()[:3]
    repeat = [int(round(ac / zc)) for zc, ac in zip(zcell, acell)]
    z = z.repeat(repeat)

    zo_inds = [atom.index for atom in z if atom.symbol == "O"]
    zt_inds = [atom.index for atom in z if atom.symbol != "O"]

    poszo = z[zo_inds].get_scaled_positions()
    poszt = z[zt_inds].get_scaled_positions()

    scaledp = atoms.get_scaled_positions()

    Dict = {}
    for a in atoms:
        pa = scaledp[a.index]
        sym = a.symbol
        if sym == "O":
            diffp = poszo - pa
            mags = [np.linalg.norm(d) for d in diffp]
            ind = mags.index(min(mags))
            ind = zo_inds[ind]
            label = all_labels[ind]

        if sym != "O":
            diffp = poszt - pa
            mags = [np.linalg.norm(d) for d in diffp]
            ind = mags.index(min(mags))
            ind = zt_inds[ind]
            label = all_labels[ind]
        Dict[a.index] = label

    return Dict


def get_unique_structures(zeolites):
    """
    Get a unique list of structures from a list of Atoms objects.
    """

    structures = [AseAtomsAdaptor().get_structure(atoms) for atoms in zeolites]
    return [
        AseAtomsAdaptor.get_atoms(s[0])
        for s in StructureMatcher().group_structures(structures)
    ]
