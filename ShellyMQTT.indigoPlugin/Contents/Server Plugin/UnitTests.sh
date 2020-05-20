#!/bin/bash
PYTHONPATH=${PWD}/tests python -m twisted.trial $(ls -1 tests/test_*.py | cut -f 1 -d '.' | sed "s/\//./g")