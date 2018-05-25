Usage
=====

Garleek is composed of two small programs:

- ``garleek-prepare``, used to patch the QM-provided input file with correct atom types
- ``garleek-backend``, which interfaces the QM program with the MM engine to make them understand each other

Usually, ``garleek-prepare`` will inject the necessary ``garleek-backend`` calls in the QM input file, so you should only run the following command. Everything else is handled automatically.

::

    garleek-prepare --qm gaussian --mm tinker --ff mm3 --types uff_to_mm3 INPUTFILE


- ``INPUTFILE``: QM input file to be patched and renamed. For example, ``file.in`` would be renamed as ``file.garleek.in``.
- ``--qm``: QM program handling the QM/MM calculation. Currently supported keywords include: *gaussian*, *gaussian_09a*, *gaussian_09b*, *gaussian_09c*, *gaussian_09d*, *gaussian_16*
- ``--mm``: MM engine to be used. Currently supported keywords include: *tinker*.
- ``--ff``: force field to be used in the MM calculation. Supported files and keywords depend on the value of ``mm``.
- ``--types``: dictionary handling the conversion between the QM-provided atom types and those the MM engine actually needs for the chosen force field. Supported files and keywords depend on the value of ``mm`` and ``qm``. Usually is a simple two-column plain-text file that contains ``QM-type MM-type`` mappings. This file is used to replace the original types in ``MyInputFile.in``. Matching is case-insensitive, but the file must list them ALWAYS uppercased.

**TIP**: Updated CLI arguments will be always available if you run ``garleek-prepare -h``.


.. note::

    For more details and specific use-cases, please refer to the tutorials section. Begin with the first one by clicking here: :ref:`tutorials`.
