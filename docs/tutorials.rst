The following tutorials assume you have already installed Garleek, Gaussian and TINKER. If that's not the case, please refer to :ref:`installation`.

.. _tutorials:

A simple CH4 molecule
---------------------

Organic species are easy to model, but with ONIOM there's always the added difficulty of setting up layers, link atoms and so on. This simple example will help describe the general workflow for setting up a two-layer QM:MM ONIOM job in GaussView.

.. tip::

    The ``tests/data/`` directory in the `Garleek source <https://github.com/insilichem/garleek/tree/master/tests/data>`_ contains several toy examples that are easy and fast to compute. Use them for your own tests and training!

01 - Build the input file
.........................

In GaussView or any similar software build a CH4 molecule and create and B3LYP/UFF ONIOM input file named ``tutorial1.in``. You should obtain something like this::

    %nprocshared=8
    %mem=8000MB
    %chk=tutorial1
    #p opt oniom(B3LYP/6-31G*:UFF) geom=connectivity

    ONIOM(QM:MM) OPT FREQ with Garleek

    0 1 0 1 0 1
     C-C_3            0    0.44534414   -2.95546554    0.00000000 H
     H-H_             0    0.80199857   -3.96427554    0.00000000 H
     H-H_             0    0.80201698   -2.45106735    0.87365150 L H-H_ 1
     H-H_             0    0.80201698   -2.45106735   -0.87365150 H
     H-H_             0   -0.62465586   -2.95545236    0.00000000 H

    1 2 1.0 3 1.0 4 1.0 5 1.0
    2
    3
    4
    5


.. note::

    In ONIOM calculations, the geometry is specified slightly differently. First, there are more than one ``charge multiplicity``. These correspond to the QM, MM real and MM model layers. Additionally, each atom line has more information:

    - The first field is usually the element symbol or its atomic number. In ONIOM, the element is extended with a second subfield for the atom type. In the first atom of the example above (``C-C_3``), ``C`` is the symbol for carbon, and ``C_3`` its UFF atom type (sp3 carbon). If the force field specified is not UFF, the atom type subfield can (and most probably will) be different.
    - A new column before the cartesian coordinates is present. Its value (``0`` or ``-1``) determines if the atom is frozen or not.
    - After the cartesian coordinates, at least one additional column is present, listing the ONIOM layer: ``H`` (high), ``M`` (middle), or ``L`` (low).
    - The layer column can be followed by the link atom specifiers, when there's a covalent bond between atoms sitting in different layers. It must contain the link atom specifier (element + atom type) and the serial index of the bonded atom. In the only example above, the link atom is a simple hydrogen atom that will replace the originally bonded carbon atom.

    The connectivity matrix is always needed because the MM program usually requires it. It lists every atom by serial number, and, if it is bonded to any atom(s), the serial number of those atoms, each followed by its corresponding bond order. In the example above, the atom 1 (carbon) is bonded to they hydrogens (atoms 2, 3, 4 and 5) with single bonds (bond order = 1.0).

This file will run just fine in Gaussian, but it will use the simple UFF force field. If you want to use a more accurate one (other than Amber and Dreiding), Garleek is needed. Let's try to use the MMFF force field for this molecule.

02 - Patch the input file with Garleek
......................................

The file as created by GaussView needs some modifications to work with Garleek. Don't worry, ``garleek-prepare`` will do everything for you! For this system to work with MM3, you would use the following command::

    garleek-prepare --qm gaussian_09d --mm tinker --ff MMFF --types uff_to_mm3 tutorial1.in

- ``--qm`` lists the QM engine in use. By default it's ``gaussian_16``, so you don't have to specify it if that's the version you are using. In this case, we are using Gaussian 09D, so that's why we included it.

- ``--mm`` lists the MM engine in use. Only TINKER is supported now, so you can omit it.

- ``--ff`` specifies the force field to be used by TINKER. The file will be found following 3 strategies:

    1. If the value is the path to a file, use it. This way you can use ``mycustomforce field.prm`` or ``mycustomparameters.key``. Both TINKER PRM and KEY files are supported.
    2. If no file is found with that path, try to find it under ``garleek/data/prm``. This allows you to use ``mm3.prm`` even if it's not present in the working directory.
    3. Try again by adding the ``.prm`` extension. This allows you to use simply ``mm3``.

- ``--types`` must be a file listing the correspondences between the atom types originally specified in the Gaussian input file, and those expected by Tinker. Since GaussView (or your favorite software) generated the types for UFF and we want to use MM3, the dictionary specified is ``uff_to_mmff``, which is included in Garleek and available in ``garleek/data/atom_types``. This option admits two types of values:

    1. A valid path to a file
    2. A filename under ``garleek/data/atom_types``.

We will go into further details later. For now, we just need to know that this command would generate a file called ``tutorial1.garleek.in`` with these contents::

    ! Created with Garleek v0+untagged.68.g6711cac.dirty
    %nprocshared=8
    %mem=8000MB
    %chk=A_1
    #p opt=nomicro oniom(B3LYP/6-31G*:external="garleek-backend --qm gaussian_09d --mm tinker --ff 'mmff'"/6-31G*) geom=connectivity

    ONIOM(QM:MM) OPT FREQ with Garleek

    0 1 0 1 0 1
     C-1              0    0.44534414   -2.95546554    0.00000000 H
     H-23             0    0.80199857   -3.96427554    0.00000000 H
     H-23             0    0.80201698   -2.45106735    0.87365150 L H-23 1
     H-23             0    0.80201698   -2.45106735   -0.87365150 H
     H-23             0   -0.62465586   -2.95545236    0.00000000 H

    1 2 1.0 3 1.0 4 1.0 5 1.0
    2
    3
    4
    5


Let's see what has changed in this file.

1. A new line beginning with an exclamation mark ``!`` has been added. This is just a comment (ignored by Gaussian) listing the garleek version used so you can reproduce the calculations later on with the exact same version.

2. The route ``#`` section has grown significantly:

    - ``opt=nomicro`` has been added. This disables microoptimizations, which can lead to known errors when applying the ``external`` keywords.
    - ``external`` has a long string attached. This is the ``garleek-backend`` command that will be called in every Gaussian ONIOM iteration. It has been added automatically by ``garleek-prepare`` so you don't need to worry about its details.
    - The basis set configured in the QM layer has been included in the MM layer as well. This is a workaround some errors with the default basis sets in Gaussian. Only applies for *exotic* elements, but since it doesn't hurt to have it specified here, it's always included for convenience.

3. The atom types (``H_``, ``C_``) has been replaced by numbers (``23``, ``1``). This is a direct replacement as specified in the ``--types`` file and it's the key step in the whole process.

03 - Review the atom types
..........................

Since this simple molecule only includes one carbon atom with its four hydrogen atoms, the conversion is trivial. UFF only includes one atom type per element, but that's very uncommon in most force fields: they will list several atom types per element depending on its bonded atoms and other conditions.

As a result, the conversion between UFF and other force fields is not unequivocal. An effort has been made to provide the best correspondence for most cases, but you should check the types manually! You can define your own atom types mapping by modifying the ones provided with Garleek (creating a separate copy is recommended) or writing a new one from scratch. The syntax is very simple: one correspondence per line, listing the original atom type in the first field, and the TINKER atom type in the second field, separated by one or more spaces. Comments can be inserted with ``#`` in its own line or ending a valid line.

For example, the ``uff_to_mm3`` file lists some correspondences between atomic numbers and default MM3 TINKER types::

    # atomic number, mm3 type, description

    1          5            # H_norm
    2          51           # He
    3          163          # Li
    4          165          # Be
    5          26           # B_sp2
    6          1            # C_sp3
    7          8            # N_sp3
    8          6            # O_sp3
    9          11           # F
    10         52           # Ne

04 - Launch the Gaussian job
............................

The resulting ``.garleek.in`` file is a valid Gaussian input file. You can run it with any standard procedures you are already using, like ``g09 tutorial2.garleek.in`` locally, or in a queued cluster system. Gaussian & Garleek will take care of the rest!

Organometallic species
----------------------

QM/MM studies are particularly useful in metal-containing systems. However, some metal elements are rarely present in MM force fields and custom parameters must be provided (especially if coordination bonds are considered in the MM part). Fortunately, most of the time you can provide an isolated metal ion (no explicit bonds for the MM calculation) and get away with providing the van der Waals radius.

Let's take the following Osmium compound as an example. Go to `tests/data/Os <https://github.com/insilichem/garleek/tree/master/tests/data/Os>`_ and grab a copy of the ``Os.in`` and ``Os.key`` files. This file can be fed to ``garleek-prepare`` to provided a Garleek-ready ``Os.garleek.in`` file::

    garleek-prepare --types uff_to_mm3 --ff Os.key Os.in

Several considerations must be done here:

- ``--types`` has been set to ``uff_to_mm3``. This file is provided with Garleek, and contains a manual mapping listing UFF to MM3 correspondences. In most cases, it should work for your needs, but you are encouraged to review the choices made in that file so they fit your system.
- ``--ff`` has been set to ``Os.key``. The ``ff`` flag can be set to either PRM or KEY files.

KEY files are important in Tinker and can help you perform a lot of calculations. We use them to load default parameters from PRM files and include additional parameters on case-by-case basis. In this example, the force field has been set to ``qmmm3.prm``. This PRM file ships with Garleek. It's an extension of the original Tinker MM3 parameters to contain atom type definitions for most elements in the periodic table (transition metals included). However, it does not contain bond, angle or dihedral parametrization. Only the element masses and VdW radii are included, so you can only use ISOLATED metal ions. If you want to use bonded MM metals, you will need to provide those parameters. The KEY file includes this data below the ``parameters`` line::

    parameters qmmm3.prm

    # Define bond parameters
    bond      7        165      0.3           1.67
    bond      8        5        6.420         1.0150
    # Define bond angle parameters
    angle     7        165      7             0.5       90.0
    angle     6        2        37            0.6       120.0
    angle     5        8        5             0.605     106.40
    # Define torsion parameters
    torsion   2   1    6    2         0.0  0.0 1    0.0 180.0 2     0.403 0.0 3
    torsion   6   2    37   37        0.0  0.0 1   12.0 180.0 2     0.0   0.0 3
    torsion   1   6    2    37        1.05 0.0 1    7.5 180.0 2    -0.2   0.0 3

Should you need more atom types, you can define those in your KEY file and provide that as the ``--ff`` value instead of a generic PRM file. For example, if you want to use the Amber99 force field with an aluminium atom, you should include two changes:

- The ``-ff`` should be a KEY file with the amber force field loaded with the ``parameters`` keyword and a new atom definition for the aluminium ion with an atom type id of your choice. Let's say ``5000``. Van der Waals data should be added as well for that atom type id.
- The ``--types`` file should list a line with ``13 5000``, where ``13`` is the Al atomic number and ``5000`` is the Tinker atom type. You an use any atom type label in the original Gaussian file (ie, ``Al-ALX``), but since Garleek will try to use the atomic number if the atom type label (``ALX``) cannot be found in the ``--types`` file, using the atomic number (``13``) works just fine as a generic fallback.

Specific details for biomolecules
---------------------------------

When biomolecules are involved in a QM/MM calculation, protein-specific force fields are needed. Fortunately, TINKER `provides several force fields <https://dasher.wustl.edu/tinker/distribution/params/>`_ that fall in this category:

- AMBER 94, 96, 98, 99, 99SB
- AMOEBABIO & AMOEBAPRO
- CHARMM 19, 22
- MM3PRO
- OPLS-AA

Protein-specific force fields usually parameterize atoms and groups them by residue. In TINKER, each atom in each residue would be a different atom type (but similar ones are grouped in atom classes). This can lead to some confusion, because TINKER will be expecting atom types, not atom classes, in its XYZ input file (this is generated automatically by Garleek). The ``--types`` dictionary will have to unequivocally map residue-atom pairs to each unique atom type. To overcome this limitation, we follow an alternative typing approach for biostructures.

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
    H-HP-0.000000(PDBName=HA2,ResName=NGL,ResNum=1)    -1   -1.50100000   20.04900000  -11.68700000 L

Notice the first *field* it's still an atom identifier whose subfields are separated by ``-`` characters:

- 1st subfield: Element symbol. Sometimes, atomic number.
- 2nd subfield: Atom type.
- 3rd subfield: Charge, ``PDB`` fields.

``PDB`` fields are **important** in Garleek because when this type of line is present, the atom type (2nd field) is IGNORED and a NEW one is computed on the fly, following this template: ``<ResName>_<PDBName>``. For example, the first line in the block above would generate an atom type named ``NGL_N``. The original ``N3`` will be IGNORED.

As a result, for the ``--types`` dictionaries to work with biomolecules, they must include the adequate ``<ResName>_<PDBName>`` combination, and not the 2nd field as seen in the previous tutorials. Obviously, the originating PDB file must have atoms and residues properly named so the PDB fields are correctly written. Otherwise, it won't work.

We provide several mappings obtained automatically from TINKER force fields featuring a ``biotype`` section using a custom script. However, for this to work, the biomolecule must include the correct ``PDBName`` and ``ResName`` values.

.. tip::

    A script named ``biotyper.py`` can be found under ``garleek/data/prm``. This script can parse PRM files for ``biotype`` lines and generate a ``.types`` file automatically, which would work as a good starting point towards configuring your own atom types mapping.

**Link atoms**

Link atoms are also affected by this special treatment. If PDB fields are present, the link atom type will be composed out of the main atom ``ResName`` and the atom type listed next to the link atom element. For example, in the line::

    H-HP-0.000000(PDBName=HA2,ResName=NGL,ResNum=1) -1 -1.50100000 20.04900000 -11.68700000 L H-HB 5

, the calculated link atom type would be ``NGL_HB``.

You should choose link atoms with type according to its bonded atom to avoid parameter problems (angles and dihedrals, particularly). For example, if the main atom is ``CB`` the correct H link atom should be ``HB``. Refer to the PRM force field to locate the proper type (PDBName).


Custom residues
...............

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

