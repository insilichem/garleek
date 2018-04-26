# Garleek: QM/MM for humans

Interface Gaussian with MM programs via `external` keyword.

## Installation

Garleek is designed to be as simple as possible, using almost no 3rd party dependencies. You only need Python (2.7 or 3.4+) and NumPy. Then, of course, you need to install the software to be interfaced. Currently, we support:

- **QM**: Gaussian 09D
- **MM**: TINKER

## Usage

Garleek comes is composed of two small programs:

- `garleek`, used to patch the QM-provided input file with correct atom types
- `garleek-backend`, which interfaces the QM program with the MM engine to make them understand each other

Usually, `garleek` will inject the necessary `garleek-backend` calls in the QM input file, so you should only run the following command. Everything else is handled automatically.

```
garleek --qm gaussian --mm tinker --ff mm3 --types uff_to_mm3 MyInputFile.in
```

- `--qm` refers to the QM program handling the QM/MM calculation
- `--mm` is the MM engine to be used
- `--ff` is the forcefield to be used in the MM calculation
- `--types` is the dictionary handling the conversion between the QM-provided atom types and those the MM engine actually needs for the chosen forcefield.
- `MyInputFile.in` is the QM input file, which will be patched and saved as `MyInputFile.garleek.in`.

## Useful resources:

Gaussian documentation for `external`: [Gaussian v16](http://gaussian.com/external/), [v09D](http://web.archive.org/web/20150906010704/http://www.gaussian.com/g_tech/g_ur/k_external.htm), [v09B](http://web.archive.org/web/20110806120317/http://www.gaussian.com/g_tech/g_ur/k_external.htm)


