#!/bin/bash

BINDIR="${0%/*}"
cd "${BINDIR}"

which pip > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python get-pip.py
  rm  get-pip.py
fi

pip install -r requirements.txt

