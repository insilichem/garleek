"""
MM
==

The ``mm`` subpackage hosts all the code that handles
calculations involving MM software.

Each module in this subpackage is expected to perform
the following tasks:

    1. Take the standardized dictionary (as explained)
       in the ``qm`` module and convert the contained
       data into the representation requested by the
       interfaced MM software (units included).
    2. Calculate the requested data (depending on
       ``derivatives`` value) with the MM software.
    3. Organize the obtained data into a standardized
       representation, as described below.

Standardized object for interfaced data
---------------------------------------

The QM engine will be expecting a dictionary containing
the following keys and values. Unit conversion is not
handled here (that's responsibility of the *connector*),
so just use those employed by the MM software (but
document those in the docstring!)

    energy : float
        Potential energy
    gradients : np.array with shape (3*n_atom,)
        Gradient on each tom
    hessian : np.array with shape (9*n_atom,)
        Flattened hessian matrix (force constants)
    dipole_moment : np.array with shape (3,), optional
        Dipole X,Y,Z-Components
    polarizability : np.array with shape (6,), optional
    dipole_derivatives : np.array with shape (9*n_atom)
        Dipole derivatives with respect to X,Y,Z components
        for each atom
"""