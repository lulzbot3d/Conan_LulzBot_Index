import sys
import yaml
import subprocess

from pathlib import Path

if __name__ == "__main__":
    recipes_paths = Path(__file__).absolute().parents[1].joinpath("recipes").glob("**/conandata.yml")
    for recipe_path in recipes_paths:
        recipe_name = recipe_path.parts[-3]
        export_path = recipe_path.parent
        with open(recipe_path, "r") as f:
            parsed_yaml = yaml.safe_load(f)
            for recipe_version in parsed_yaml["sources"].keys():
                subprocess.run(f"conan export {export_path} {recipe_name}/{recipe_version}@{sys.argv[1]}/{sys.argv[2]}", shell = True)
