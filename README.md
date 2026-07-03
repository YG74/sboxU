# sboxU

![The logo of sboxU, showing a box being built or disassembled.](./docs/source/logo-v2-5.png)

## Description


`sboxU` is a SAGE/Python library that is intended to systematize knowledge about the black-box analysis of vectorial Boolean functions, p-ary fuctions, and in particular about the algorithms relevant to their study. To this end, it provides a wide variety of functions performing for instance the following tasks:
- generating S-boxes from univariate polynomials,
- multi-threaded computation of the Walsh spectrum,
- display of the "Pollock representation" of a DDT,
- computation of the automorphisms of the graph of an APN function,
- identify all the bijections in the CCZ-equivalence class of a function,
- computation of the non-linear invariants of a function,
- ... and much, much more!

At its core, `sboxU` is a C++ library providing convenient abstractions for S-boxe, affine maps, etc.; as well as the algorithms operating on them. Then, a cython layer exposes these functions to SAGE.

## Affine Equivalence Speed Optimization (this fork)

This fork contains a major speed optimization of the affine equivalence check (Biryukov algorithm) for 8-bit permutation S-boxes.

- **Speedup**: total check time reduced from **~2720 ms** to **~0.300 ms** (≈99.99% faster).
- **Benchmark scenarios**:
  - `aes_self`: AES S-box self-equivalence — ~0.17 ms
  - `random_self`: random permutation self-equivalence — ~0.12 ms
  - `random_nonequiv`: non-equivalent random pair — ~0.009 ms
- **Key techniques kept**:
  - OpenMP parallelization of linear class representatives
  - Link-time optimization (`-flto`)
  - Differential spectrum filter for fast non-equivalent rejection
  - `std::unordered_map` and flat vectors replacing ordered maps
  - AVX2 SIMD for lexicographic comparison
  - Self-equivalence fast path with byte comparison
  - Incremental differential spectrum comparison
  - Cache-friendly state representation and pruning
- **Correctness**: verified with `experiments/affine-equivalence/benchmark.py --verify` and `tests/ccz/test_ea_mapping_from_vq.py`. A batch of post-optimization micro-optimizations introduced a correctness regression and was reverted; the current state is the last known-good, passing commit.
- **Details**: see `experiments/affine-equivalence/STRATEGY.md` and `experiments/affine-equivalence/results.tsv` for the full experiment log.

If you use `sboxU` in a published paper, please cite it using the following bibtex entry:

```
    @misc{sboxU,
    authors={Léo Perrin,
    Jens Alich,
    Jules Baudrin,
    Aurélien Boeuf,
    Xavier Bonnetain,
    Alain Couvreur,
    Merlin Fruchon,
    Mathias Joly,
    Pierre Galissant,
    Lukas Stennes
    },
    year=2026,
    title={sbox{U}: black-box analysis of discrete functions},
    howpublished={Available online at \url{https://github.com/lpp-crypto/sboxU/}}
    }
```



### Documentation 

Some tests/examples are provided in the `tests` folder. You must compile and install `sboxU` as explained below in order for them to work. 

- The SAGE API is documented [here](https://who.paris.inria.fr/Leo.Perrin/code/sboxU/sage/) (note in particular the search box!).
- If you need direct access to its C++ internals, a (still quite incomplete) API documentation is available [here](https://who.paris.inria.fr/Leo.Perrin/code/sboxU/cpp/).



### sboxU_CPP

The `C++` component of `sboxU` can be used on its own, see [the relevant folder](./sboxUv2/cpp/README.md).

### Executable Scripts

During its installation, `sboxU` creates some executables that are installed in your path. To see their interfacce, simply run them with the `-h` argument.

- **sboxU_apn_db_generation** uses known lists of APN fuctions to generate a local `tinySQL` database containing exactly one representstive per EA-class of functions 


## Installing SboxU


### Dependencies

Most functions in `sboxU` only depend on a recent version of SAGE (it was tested for example with version 10.5). Some use `openmp` for multithreading, and you may need to install it in order to successfully compile. The python dependencies are installed automatically by `pip`.

Installing openmp can be done with:

    sudo apt-get install libomp-dev

or, on macOS:

    brew install libomp


### Downloading and Compiling


#### Straight from Github 

To be able to use `sboxU` in your scripts, simply run the following command. It will download and compile `sboxU` (and also create some executable scripts, see above).

```
sage -pip install git+https://github.com/lpp-crypto/sboxU
```

#### From a Local Copy of the Repository

Alternatively, especially if you want to work on `sboxU`, you can first clone this repository and then install `sboxU` from its content. To do this, simply `cd` to the directory containing this makefile and run

```
sage -pip install -e .
```

Once it has been installed, you can recompile it much faster using

```
sage setup.py build_ext --inplace -j 8
```


## Contributing

### How to

TODO

### Contributors

- [Jens Alich](https://informatik.rub.de/ac-personen/alich/)
- [Jules Baudrin](https://who.paris.inria.fr/Jules.Baudrin/)
- [Aurélien Boeuf](https://who.paris.inria.fr/Aurelien.Boeuf/)
- [Xavier Bonnetain](https://bonneta.in/)
- [Alain Couvreur](http://www.lix.polytechnique.fr/Labo/Alain.Couvreur/)
- [Mathias Joly](https://github.com/MathiasJoly)
- [Merlin Fruchon](https://who.paris.inria.fr/Merlin.Fruchon/)
- [Pierre Galissant](https://314gali.github.io/)
- [Léo Perrin](https://who.paris.inria.fr/Leo.Perrin/)
- [Lukas Stennes](https://informatik.rub.de/symcrypt/personen/stennes/)





