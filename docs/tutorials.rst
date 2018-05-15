.. _tutorials:

Tutorials
=========

.. note::

    The following tutorials assume you have already installed Garleek, Gaussian and TINKER. If that's not the case, please refer to :ref:`installation`.

Gaussian-Tinker ONIOM
---------------------

Simple organic molecule
.......................

Organic species are easy to model, but with ONIOM there's always the added difficulty of setting up layers, link atoms and so on. This simple example will help describe the general workflow for setting up a two-layer QM:MM ONIOM job in GaussView.



Organometallic species
......................

WIP!

Protein-ligand structure
........................

When biomolecules are involved in a QM/MM calculation, protein-specific forcefields are needed. Fortunately, TINKER `provides several forcefields <https://dasher.wustl.edu/tinker/distribution/params/>`_ that fall in this category:

- AMBER 94, 96, 98, 99, 99SB
- AMOEBABIO & AMOEBAPRO
- CHARMM 19, 22
- MM3PRO
- OPLS-AA

Protein-specific forcefields usually parametrize atoms and groups them by residue. In TINKER, each atom in each residue would be a different atom type (but similar ones are grouped in atom classes). This can lead to some confusion, because TINKER will be expecting atom types, not atom classes, in its XYZ input file (this is generated automatically by Garleek). The ``--types`` dictionary will have to unequivocally map residue-atom pairs to each unique atom type. To overcome this limitation, we follow an alternative typing approach for biostructures.


.. tip::

    To prepare a protein structure, using separate software like UCSF Chimera with our Tangram suite is recommended. This will take care of some annoying details that have to do with atom typing, like adding hydrogen atoms and terminal caps should be added, or fixing residue and atom names, and generate the properly formatted Gaussian input file Garleek expects.

When the protein structure is properly formatted, you should obtain a PDB file that can be loaded into GaussView. Instead of having atom lines like these:

::

    C-C_3            0    0.44534414   -2.95546554    0.00000000 H
    H-H_             0    0.80199857   -3.96427554    0.00000000 H
    H-H_             0    0.80201698   -2.45106735    0.87365150 L H-H_ 1
    H-H_             0    0.80201698   -2.45106735   -0.87365150 H
    H-H_             0   -0.62465586   -2.95545236    0.00000000 H

You will see lines like these:

::

    N-N3-0.000000(PDBName=N,ResName=NGL,ResNum=1)      -1   -0.47100000   20.52700000  -13.50600000 L
    H-H-0.000000(PDBName=H1,ResName=NGL,ResNum=1)      -1   -0.31300000   21.51500000  -13.64700000 L
    H-H-0.000000(PDBName=H2,ResName=NGL,ResNum=1)      -1    0.26700000   20.00100000  -13.95200000 L
    H-H-0.000000(PDBName=H3,ResName=NGL,ResNum=1)      -1   -1.36000000   20.26700000  -13.90800000 L
    C-CX-0.000000(PDBName=CA,ResName=NGL,ResNum=1)     -1   -0.48000000   20.22400000  -12.02500000 L
    H-HP-0.000000(PDBName=HA2,ResName=NGL,ResNum=1) -1 -1.50100000 20.04900000 -11.68700000 L

Notice the first *word* it's still an atom identifier whose fields are separated by ``-`` characters:

- 1st field: Element symbol. Sometimes, atomic number.
- 2nd field: Atom type.
- 3rd field: Charge, ``PDB`` fields.

``PDB`` fields are **important** in Garleek because when this type of line is present, the atom type (2nd field) is IGNORED and a NEW one is computed on the fly, following this template: ``<ResName>_<PDBName>``. For example, the first line in the block above would generate an atom type named ``NGL_N``. The original ``N3`` will be IGNORED.

As a result, for the ``--types`` dictionaries to work with biomolecules, they must include the adequate ``<ResName>_<PDBName>`` combination, and not the 2nd field as seen in the previous tutorials. Obviouslt, the originating PDB file must have atoms and residues properly named so the PDB fields are correctly written. Otherwise, it won't work.

We provide several mappings obtained automatically from TINKER forcefields featuring a ``biotype`` section using a custom script. However, for this to work, the biomolecule must include the correct ``PDBName`` and ``ResName`` values..

.. note::

    Take into account that link atoms are also affected by this special treatment. You should choose link atoms with type according to its bonded atom. For example, if bonded atom is ``CB`` the correct H link atom should be ``HB``. Refer to the PRM forcefield to locate it.

Custom residues
~~~~~~~~~~~~~~~

When custom residues are present in the structure, even in the QM region, they must be included for the MM calculation anyways. Using them is no harder than normal residues, but parameters must be present either in the PRM file or in a custom KEY file. Then, the normal atom type conversion rules will be followed to locate the proper TINKER atom type from the PDB fields.

Toy example for a NH3 residue in the Amber format:

The PDB file would be something like this::

    HETATM    1  N1  NH3     1       0.000   0.000   0.000  1.00  0.00           N
    HETATM    2  H1  NH3     1       1.010   0.000   0.000  1.00  0.00           H
    HETATM    3  H2  NH3     1      -0.337   0.952   0.000  1.00  0.00           H
    HETATM    4  H3  NH3     1      -0.336  -0.476  -0.825  1.00  0.00           H

The Gaussian input file would end up like::

    N-N3-0.000000(PDBName=N1,ResName=NH3,ResNum=1)      -1   0.000   0.000   0.000 L
    H-HN-0.000000(PDBName=H1,ResName=NH3,ResNum=1)      -1   1.010   0.000   0.000 L
    H-HN-0.000000(PDBName=H2,ResName=NH3,ResNum=1)      -1  -0.337   0.952   0.000 L
    H-HN-0.000000(PDBName=H3,ResName=NH3,ResNum=1)      -1  -0.336  -0.476  -0.825 L

The PRM file should contain:

::

    atom    5000   14    N     "Custom Residue NH3 N1"       7    14.010    3
    atom    5001   29    H     "Custom Residue NH3 H1"       1     1.008    1
    atom    5002   29    H     "Custom Residue NH3 H2"       1     1.008    1
    atom    5003   29    H     "Custom Residue NH3 H3"       1     1.008    1

    # bonds, dihedrals, vdw and so on should be needed as well
    # You would probably use something like Antechamber for these data

The ``--types`` dictionary should list:

::

    UNK_N1 5000
    UNK_H1 5001
    UNK_H2 5002
    UNK_H3 5003

