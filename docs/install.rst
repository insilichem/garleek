.. _installation:

Installation
============

Garleek is designed to be as simple as possible, using almost no 3rd party dependencies. You only need Python (2.7 or 3.4+) and NumPy. This can be easily achieved with ``pip``:

::

    # Stable version
    python -m pip install garleek
    # Latest, development version (might be unstable)
    python -m pip install -U https://github.com/insilichem/garleek/archive/master.zip


Testing
-------

Unit-tests are provided in the ``tests/`` directory. Structures included are very small (5-20 atoms), so it should run reasonably fast locally. Input files are adjusted for 8 CPUs and 8GB RAM. To run them, you must install additional dependencies::

    pip install pytest cclib

Additionally, the interfaced software must be properly initialized (ie, executables should be available in ``$PATH``, any needed environment variable exported, etc.). To do this, you'd normally use ``module load`` or similar utilities. An example on how to prepare the testing environment is provided in ``tests/run.sh``. Feel free to modify it to your own needs.