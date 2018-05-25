Introduction
============

Garleek allows you to perform QM/MM calculations by interfacing Gaussian with MM programs via its ``external`` keyword.

.. _supported-software:

Supported software
------------------

Garleek currently supports the following programs. It expects them to be available in ``$PATH``.

QM engines
..........

- Gaussian 16
- Gaussian 09A, 09B, 09C, 09D

MM engines
..........

- TINKER 8.1 (only ``analyze``, ``testgrad`` and ``testhess`` are needed)


How does it work
----------------

Let's explain it with an example: doing an ONIOM calculation with Gaussian
and TINKER.

When Garleek does an ONIOM calculation with Gaussian & TINKER, Gaussian
handles the majority of the calculations: QM stuff and ONIOM scheme. The MM
part is configured with the ``external`` keyword, which specifies that the MM
calculations will be performed with an external program. In this mode, Gaussian
will write a series of files to disk and call the requested program.

In this case, it's ``garleek-backend``, which will take one of the files Gaussian
generates in each iteration (the ``*.EIn`` file), transform it and pass it to TINKER
binaries to obtain the requested data: potential energy, dipole moment, polarizability
and/or hessian matrix, depending on the calculation. Gaussian expects these data written
back to an ``*.EOu`` file in a `very specific format <http://gaussian.com/external/>`_.

In a nutshell, all Garleek does is interfacing Gaussian and TINKER following the
``external`` protocol:

1. Parse Gaussian's ``EIn`` files
2. Convert to whatever the MM engine is expecting
3. Calculate the requested data (defined in the ``EIn`` header)
4. Convert the obtained MM data to Gaussian units and write it to the ``EOu`` file

The main difficulty here is making sure that the atom types are understandable by both
parts of the scheme: the Gaussian input file should contain atom types compatible with
the MM engine. Since this is rarely the case, a previous step is needed: patching the
original Gaussian file so it contains adequate atom types. We take advantage of this step
to inject the correct ``garleek-backend`` calls in the ``external`` keyword so the user
does not have to worry about those details. For further information on the practical usage,
please read our Tutorials section. First one: :ref:`tutorials`.

