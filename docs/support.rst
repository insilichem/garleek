Citation & Funding
==================

Garleek is scientific software, funded by public research grants: Spanish MINECO (project ``CTQ2017-87889-P``, ``CTQ2017-87792‐R``, Severo Ochoa Excellence Accreditation 2014–2018 ``SEV‐2013‐0319``), Generalitat de Catalunya (project ``2014SGR989``, CERCA Programme); J.R.-G.P.: Generalitat de Catalunya (grant ``2017FI_B2_00168``); I.F.-A.: Spanish MINECO (Severo Ochoa predoctoral training fellowship ``SVP‐2014–068662``). If you make use of Garleek in scientific publications, please link back to this repository (a publication is under preparation). It will help measure the impact of our research and future funding!


Help & Support
==============

If you have any question, doubt or suggestion, please `submit an issue <https://github.com/insilichem/garleek/issues>`_ in our GitHub repository.


Frequently Asked Questions
--------------------------


Where can I found Gaussian's documentation for ``external`` keyword?
....................................................................

Follow these links: `Gaussian v16 <http://gaussian.com/external>`_, `v09D <http://web.archive.org/web/20150906010704/http://www.gaussian.com/g_tech/g_ur/k_external.htm>`_,  `v09B <http://web.archive.org/web/20110806120317/http://www.gaussian.com/g_tech/g_ur/k_external.htm>`_,  `v03 <http://www.lct.jussieu.fr/manuels/Gaussian03/g_ur/k_external.htm>`_


Why don't you support more MM software?
.......................................

Please, follow the ongoing discussion `in this issue <https://github.com/insilichem/garleek/issues/1>`_. PRs are welcome!

Common Garleek/Gaussian/Tinker errors
.....................................

Garleek only provides a light wrapper around Gaussian's ``external`` keyword, so it still uses Gaussian's ONIOM implementation, which can be a bit picky depending on the requested operations. MM is tricky itself if the parameters are not available. The list below provides some common errors we have found in our ONIOM journey. It's not meant to be exhaustive, but a collection of the results of long debugging sessions.

Gaussian complains about basis sets not being available
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even though the MM calculation needs no basis sets, Gaussian still runs ``l301`` on the MM part, which is responsible for preparation tasks like basis sets reading. If your system contains *exotic* elements (say, Rhenium or Osmium) and you are already using ``genecp``, it won't find compatible basis sets. The solution is to provide the basis sets manually by appending the ``gen`` option to the external call and appending two additional basis sets sections (but no pseudopotentials!) around the original basis set section corresponding to the QM ``genecp`` basis sets. Since this task is repetitive and prone to error, Garleek will do it for you. If ``gen`` or ``genecp`` options are present in the ``ONIOM()`` call, the ``external`` option will be patched with the ``gen`` keyword and the basis sets section will be amended as needed. Similarly, if the basis set is globally specified directly in the ``ONIOM()`` call (no ``genecp`` nor ``gen`` keywords, but a specific basis set like ``6-31G*``), it will be added to the ``external`` option just in case. When this patch is applied, you will get an informative message in the output. See ``tests/data/Os/Os.in`` for an example input file what will benefit from this correction.

Gaussian says "MOMM, but no IMMCRS"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opt=nomicro`` is almost compulsoryin optimization jobs. Garleek will try to add it automatically if it's not present, but it might fail in some cases. Please check the option is there in the route section.

Garleek-prepare says "KeyError: 75 not found in line XXXXX"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The atom type ``XX`` is not listed in the provided ``--types`` file. Due to Garleek fallback strategies, ``XX`` can be the atom type label (ie, ``C-XX 0.000 1.000 2.000`` in the cartesian geometry specification) or the atomic number corresponding to that element.

This ``--types`` file must list atom type correspondences between the originally present atom type labels in the Gaussian input and the atom types Tinker is expecting. This way, ``garleek-prepare`` can replace them in the file and provide the Tinker ones in the patched ``garleek.in`` file. If you are using custom residues, you must make sure the Tinker atom type and its parameters is correctly defined in the PRM or KEY file (specified as the ``--ff`` flag).

Tinker says "Unusual number of connected atoms"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The atom type specified for that atom center does not expect covalently bonded species and is missing the bond parameters. You can either (a) provide those parameters or (b) delete the involved bonds in the connectivity section (by hand or in GaussView).