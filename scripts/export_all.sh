#!/bin/bash

# Exports all recipes found in the recipe folder

pushd .
cd ../recipes
find . -maxdepth 1 -type d \( ! -name . \) -exec bash -c "conan export {}" \;
popd
