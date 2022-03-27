"""Usage:
  create_pypi_recipe.py <name> <version> <location>
  create_pypi_recipe.py -h | --help | --version
"""
import requests

from pathlib import Path

from jinja2 import Template
from docopt import docopt

def main(name: str, version: str, location: str):
    resp = requests.get(f"https://pypi.org/pypi/{name}/json").json()
    jinja_template_path = Path(__file__).resolve().parent.joinpath("pypi.jinja")

    if resp["info"]["requires_dist"] is not None:
        requirements = ",\\\n                "
        for requirement in resp["info"]["requires_dist"]:
            req = requirement.split(";")  # TODO: take options into account
            r = req[0].split(" (")
            if len(r) == 2:
                v = "[" + r[1][:-1].replace(" ", "").replace(",", " ") + "]"
            else:
                v = "[>=0.0.0]"
            requirements += f"\"{r[0].replace(' ', '')}/{v}@python/stable\",\n                "
        if len(requirements) > 19:
            requirements = requirements[:-19]
    else:
        requirements = ""

    result = ""
    with open(jinja_template_path, "r") as f:
        tm = Template(f.read())
        result = tm.render(name = name,
                           package_name = name.capitalize(),
                           version = version,
                           description = resp["info"].get("summary", ""),
                           license = resp["info"].get("license", ""),
                           homepage = resp["info"].get("home_page", ""),
                           url = resp["info"].get("project_urls", {}).get("Homepage", ""),
                           requirements = requirements.lower(),
                           )
        result_path = Path(location)
        result_path.mkdir(exist_ok = True)
        conanfile_path = result_path.joinpath("conanfile.py")
        conanfile_path.unlink(missing_ok = True)
        print(f"Writing conanfile to: {conanfile_path}")
    with open(conanfile_path, "w") as f:
        f.write(result)

if __name__ == '__main__':
    kwargs = docopt(__doc__, version='0.1.0')
    main(name = kwargs["<name>"], version = kwargs["<version>"], location = kwargs["<location>"])

# TODO: Handle hashes
