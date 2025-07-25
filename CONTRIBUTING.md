# Contributing

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at [https://github.com/python-attrs/cattrs/issues](https://github.com/python-attrs/cattrs/issues).

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

_cattrs_ could always use more documentation, whether as part of the
official cattrs docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at [https://github.com/python-attrs/cattrs/issues](https://github.com/python-attrs/cattrs/issues).

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up _cattrs_ for local development.

1. Fork the `cattrs` repo on GitHub.
2. Clone your fork locally::

```shell
$ git clone git@github.com:your_name_here/cattrs.git
```

3. Install your local copy into a virtualenv. Assuming you have [uv](https://docs.astral.sh/uv/) installed, this is how you set up your fork for local development::

```shell
$ cd cattrs/
$ uv sync --all-groups --all-extras
```

4. Create a branch for local development::

```shell
$ git switch -c name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

5. When you're done making changes, check that your changes pass lints and the tests, including testing other Python versions::

```shell
$ just lint
$ just test
$ just --set python python3.9 test  # Test on other versions
```

6. Write any necessary documentation, including updating the changelog (HISTORY.md). The docs can be built like so:

```shell
$ just docs
$ just htmllive  # Build the docs, serve then and autoreload on changes
```

7. Commit your changes and push your branch to GitHub::

```shell
$ git add .
$ git commit -m "Your detailed description of your changes."
$ git push origin name-of-your-bugfix-or-feature
```

8. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for all supported Python versions. Check
   [https://github.com/python-attrs/cattrs/actions](https://github.com/python-attrs/cattrs/actions)
   and make sure that the tests pass for all supported Python versions.
4. Don't forget to add a line to HISTORY.md.

## Tips

To run a subset of tests:

```shell
$ just test tests/test_unstructure.py
```
