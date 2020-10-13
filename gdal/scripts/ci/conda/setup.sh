#!/bin/bash

conda update -n base -c defaults conda -y
conda install conda-build ninja compilers -y

pwd
ls
git clone https://github.com/conda-forge/gdal-feedstock.git

cd gdal-feedstock
cat > recipe/recipe_clobber.yaml <<EOL
source:
  git_url: https://github.com/hobu/gdal.git
  git_rev: ${GITHUB_SHA}
  url:
  sha256:

build:
  number: 2112
EOL

ls recipe
