"""Usage:
  create_pypi_conandata.py <name> <location>
  create_pypi_conandata.py -h | --help | --version
"""
import requests
import yaml

from pathlib import Path

from docopt import docopt


def main(name: str, location: str):
    resp = requests.get(f"https://pypi.org/pypi/{name}/json").json()

    conandata = {}
    if resp["releases"] is not None:
        for release, release_data in resp["releases"].items():
            for data in release_data:
                if data["packagetype"] == "bdist_wheel":
                    conandata[release] = {"url": data["url"], "sha256": data["digests"]["sha256"]}

        result_path = Path(location)
        result_path.mkdir(exist_ok = True)
        conandata_path = result_path.joinpath("conandata.yml")
        conandata_path.unlink(missing_ok = True)
        print(f"Writing conandata to: {conandata_path}")
        with open(conandata_path, "w") as f:
            yaml.dump({"sources": conandata}, f)


if __name__ == '__main__':
    kwargs = docopt(__doc__, version = '0.1.0')
    main(name = kwargs["<name>"], location = kwargs["<location>"])
