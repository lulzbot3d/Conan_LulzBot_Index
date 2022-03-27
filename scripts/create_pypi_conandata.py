"""Usage:
  create_pypi_conandata.py <name> <location>
  create_pypi_conandata.py -h | --help | --version
"""
import requests
import yaml

from pathlib import Path

from docopt import docopt


def quoted_presenter(dumper, data):
    # define a custom representer for strings, needed because the Conan parse could otherwise interpret version numbers
    # as numeric values. See https://docs.conan.io/en/1.45/reference/config_files/conandata.yml.html
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


yaml.add_representer(str, quoted_presenter)


def main(name: str, location: str):
    resp = requests.get(f"https://pypi.org/pypi/{name}/json").json()

    conandata = {}
    if resp["releases"] is not None:
        for release, release_data in resp["releases"].items():
            for data in release_data:
                if data["packagetype"] == "bdist_wheel":
                    conandata[str(release)] = {"url": data['url'], "sha256": str(data["digests"]["sha256"])}

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
