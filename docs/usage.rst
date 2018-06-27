Usage
=====

Garleek is composed of two small programs:

- ``garleek-prepare``, used to patch the QM-provided input file with correct atom types
- ``garleek-backend``, which interfaces the QM program with the MM engine to make them understand each other

Usually, ``garleek-prepare`` will inject the necessary ``garleek-backend`` calls in the QM input file, so you should only run the following command. Everything else is handled automatically.

::

    garleek-prepare --qm gaussian --mm tinker --ff mm3 --types uff_to_mm3 INPUTFILE


- ``INPUTFILE``: QM input file to be patched and renamed. For example, ``file.in`` would be renamed as ``file.garleek.in``. Currently supported: Gaussian input files (``.gjf``, ``.com``, ``.in``).
- ``--qm``: QM program handling the QM/MM calculation. Currently supported keywords include: *gaussian*, *gaussian_09a*, *gaussian_09b*, *gaussian_09c*, *gaussian_09d*, *gaussian_16*.
- ``--mm``: MM engine to be used. Currently supported keywords include: *tinker*, *tinker_qmcharges*. Read below for more details.
- ``--ff``: force field to be used in the MM calculation. Supported files and keywords depend on the value of ``mm``.
- ``--types``: dictionary handling the conversion between the MM atom types provided in the original input file and those the MM engine actually needs for the chosen force field. Supported files and keywords depend on the value of ``mm`` and ``qm``. Usually is a simple two-column plain-text file that contains ``Original-MM-type Converted-MM-type`` mappings. This file is used to replace the original types in ``MyInputFile.in``. Matching is case-insensitive, but the file must list them ALWAYS uppercased.

**TIP**: Updated CLI arguments will be always available if you run ``garleek-prepare -h``.


.. note::

    For more details and specific use-cases, please refer to the tutorials section. Begin with the first one by clicking here: :ref:`tutorials`.


About --qm and --mm tags
------------------------

These flags (``--qm`` and ``--mm``) are used to guarantee that the two programs involved are compatible. They expect a value formatted like this::

    <program>[_<version>]

Valid values include ``gaussian``, ``tinker``, ``gaussian_16`` and ``tinker_8``. The version can be omitted and will default to the latest supported (Gaussian 16 and Tinker 8.2, for example). We use the version to customize the behavior of the ``garleek-backend`` executable. For example, Gaussian 09A generates slightly different exchange files than Gaussian 09B and above, so we use the version tag to enable a different parser.

The ``version`` does not need to be a number; in fact, we can use it to provide different behaviors as well. Available versions are listed ``garleek/{qm,mm}/<program>.py``. Their behavior is documented below:

Gaussian
........

- ``gaussian``, ``gaussian_09b``, ``gaussian_09c``, ``gaussian_09d``, ``gaussian_16``: Default behavior.
- ``gaussian_09a``: Different ``EIn`` parser.

Tinker
......

- ``tinker``, ``tinker_8``, ``tinker_8.1``: Default behavior.
- ``tinker_qmcharges``: Use charges provided in the QM input file, instead of the one available in the PRM or KEY files. For this to work, a new KEY ``garleek.charges.key`` file is generated on the fly for each iteration, containing the appropriate ``CHARGE SERIAL_NUMBER VALUE`` lines.