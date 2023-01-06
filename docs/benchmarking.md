# Benchmarking

cattrs includes a benchmarking suite to help detect performance regressions and
guide performance optimizations.

The suite is based on pytest and pytest-benchmark. Benchmarks are similar to
tests, with the exception of being stored in the `bench/` directory and being
used to verify performance instead of correctness.

## A Sample Workflow

First, ensure the system you're benchmarking on is as stable as possible. For
example, the pyperf library has a `system tune` command that can tweak
CPU frequency governors. You also might want to quit as many applications as
possible and run the benchmark suite on isolated CPU cores (`taskset` can be
used for this purpose on Linux).

Then, generate a baseline using `make bench`. This will run the benchmark suite
and save it into a file.

Following that, implement the changes you have in mind. Run the test suite to
ensure correctness. Then, compare the performance of the new code to the saved
baseline using `make bench-cmp`. If the code is still correct but faster,
congratulations!
