from __future__ import annotations

import os

import numpy as np
from ase import Atoms
from ase.io import write



def count_rings(paths):
    Class = []
    for p in paths:
        Class.append(int(len(p) / 2))

    paths = [x for _, x in sorted(zip(Class, paths), reverse=True)]
    Class.sort(reverse=True)

    class_count = []
    for i in range(len(Class)):
        if i == 0:
            class_count.append(1)
        else:
            counter = 1
            for j in range(i):
                if Class[i] == Class[j]:
                    counter += 1
            class_count.append(counter)

    return Class, class_count, paths


def add_cation(
    atoms,
    large_atoms,
    radii,
    index,
    symbol,
    paths,
    included_rings,
    class_count,
    path=None,
    bvect=None,
):
    traj = []
    locations = []
    for i in range(len(paths)):
        p = paths[i]
        if len(p) in included_rings:
            trans = atoms[index].position - large_atoms[index].position
            positions = large_atoms[p].positions
            co = sum(positions) / len(positions)
            co += trans
            vector = co - atoms[index].position
            vector = np.array(vector)
            vhat = vector / np.linalg.norm(vector)

            if bvect:
                bond_length = bvect
            else:
                bond_length = radii[symbol] + 2 / radii[symbol]

            new_p = [atoms[index].position + bond_length * vhat]

            adsorbate = Atoms(symbol)
            adsorbate.set_positions(new_p)
            c_atoms = atoms + adsorbate
            c_atoms.wrap()
            traj += [c_atoms]
            locations.append(f"{int(len(p) / 2)!s}MR")
            # write POSCAR for each structure

            if path:
                os.makedirs(
                    f"{path}/D-{int(len(p) / 2)!s}MR-{class_count[i]!s}",
                    exist_ok=True,
                )

                write(
                    f"{path}/D-{int(len(p) / 2)!s}MR-{class_count[i]!s}/POSCAR",
                    c_atoms,
                    sort=True,
                )
    return traj, locations
