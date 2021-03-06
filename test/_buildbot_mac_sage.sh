#!/bin/bash
set -e
rm -rf ${HOME}/.matplotlib/*
rm -rf build

export PATH=${HOME}/dev/bin:$PATH
export PYTHON=${HOME}/dev/bin/python
export PREFIX=${HOME}/devbb 
export PYTHONPATH=${PREFIX}/lib/python2.6/site-packages:${HOME}/dev/lib/python2.6/site-packages

make -f make.osx mpl_install
echo ${PYTHONPATH}

cd test
rm -f failed-diff-*.png
python -c "import sys, matplotlib; success = matplotlib.test(verbosity=2); sys.exit(not success)"
