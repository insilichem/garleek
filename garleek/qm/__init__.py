"""
qm/
===

The ``qm`` subpackage hosts all the code that handles
calculations involving QM software.

All modules listed here are expected to perform the
following tasks:

- Patch the INPUT file with proper ``garleek-backend``
  calls and atom type conversion.
- Parse the intermediate files as provided by the QM
  software into a standardized object (details below).
- Write the output file expected by the QM software.
- List supported versions and the default ones in two
  tuples named ``supported_versions`` and
  ``default_version``, respectively.

Standardized object for interfaced data
---------------------------------------

The intermediate representation of the parsed data, which
will be passed to the MM engine, should be a dict with these
keys and values:

    n_atoms : int
        Number of atoms in the structure or substructure
    derivatives : int
        Calculations requested for the MM part:

        - ``0``: energy only
        - ``1``: calculate gradient
        - ``2``: calculate hessian

        These values are cumulative, so if ``2`` is requested,
        ``0`` and ``1`` should be computed as well.
    charge : float
        Global charge of the structure
    spin : int
        Multiplicity of the system
    atoms : OrderedDict of dicts
        Ordered dictionary mapping atom index with another
        dictionary containing these values:

        - ``element`` : ``str``. Chemical element
        - ``type`` : ``str``. Atom type as expected by the MM part
        - ``xyz`` : ``np.array`` with shape (3,). Cartesian coordinates
        - ``mm_charge`` : ``float``. Atom point charge for the MM part

    bonds : OrderedDict of lists of 2-tuples
        Ordered dictionary mapping atom-index to a list of
        2-tuples containing bonded atom index (int) and
        bond order (float)

"""