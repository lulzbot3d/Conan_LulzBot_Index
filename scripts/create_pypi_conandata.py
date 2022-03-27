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
                    split_filename = data["filename"].removesuffix(".whl").split("-")
                    print(split_filename)
                    if str(release) not in conandata:
                        conandata[str(release)] = {}

                    if "abi3" in split_filename[-2] or "cp" in split_filename[-2] or "none" in split_filename[-2]:
                        # This wheel distribution is universal or CPython ABI compatible
                        if "py" in split_filename[-3] or "cp" in split_filename[-3]:
                            # This wheel distribution is Python compatible
                            python_version = split_filename[-3].split(".")[-1][2:]
                            if len(python_version) > 1:
                                python_version = python_version[0] + "." + python_version[1:]
                            else:
                                python_version = python_version + ".0"

                            if "any" == split_filename[-1]:
                                if "Any" not in conandata[str(release)]:
                                    conandata[str(release)]["Any"] = {}

                                if python_version not in conandata[str(release)]["Any"]:
                                    conandata[str(release)]["Any"][python_version] = {}

                                conandata[str(release)]["Any"][python_version]["url"] = data["url"]
                                conandata[str(release)]["Any"][python_version]["sha256"] = str(data["digests"]["sha256"])

                            if "manylinux" in split_filename[-1]:
                                if "Linux" not in conandata[str(release)]:
                                    conandata[str(release)]["Linux"] = {}

                                if python_version not in conandata[str(release)]["Linux"]:
                                    conandata[str(release)]["Linux"][python_version] = {}

                                if "x86_64" in split_filename[-1]:
                                    conandata[str(release)]["Linux"][python_version]["url"] = data["url"]
                                    conandata[str(release)]["Linux"][python_version]["sha256"] = str(data["digests"]["sha256"])

                            if "macosx" in split_filename[-1]:
                                if "Darwin" not in conandata[str(release)]:
                                    conandata[str(release)]["Darwin"] = {}

                                if python_version not in conandata[str(release)]["Darwin"]:
                                    conandata[str(release)]["Darwin"][python_version] = {}

                                if "x86_64" in split_filename[-1]:  # Prefer x86_64 over
                                    conandata[str(release)]["Darwin"][python_version]["url"] = data["url"]
                                    conandata[str(release)]["Darwin"][python_version]["sha256"] = str(data["digests"]["sha256"])
                                elif "intel"in split_filename[-1]:
                                    conandata[str(release)]["Darwin"][python_version]["url"] = data["url"]
                                    conandata[str(release)]["Darwin"][python_version]["sha256"] = str(data["digests"]["sha256"])
                                elif "universal2" in split_filename[-1]:
                                    conandata[str(release)]["Darwin"][python_version]["url"] = data["url"]
                                    conandata[str(release)]["Darwin"][python_version]["sha256"] = str(data["digests"]["sha256"])

                            if "win_amd64" in split_filename[-1]:
                                if "Windows" not in conandata[str(release)]:
                                    conandata[str(release)]["Windows"] = {}

                                if python_version not in conandata[str(release)]["Windows"]:
                                    conandata[str(release)]["Windows"][python_version] = {}

                                conandata[str(release)]["Windows"][python_version]["url"] = data["url"]
                                conandata[str(release)]["Windows"][python_version]["sha256"] = str(data["digests"]["sha256"])

        result_path = Path(location)
        result_path.mkdir(exist_ok = True)
        conandata_path = result_path.joinpath(name, "conandata.yml")
        conandata_path.unlink(missing_ok = True)
        print(f"Writing conandata to: {conandata_path}")
        with open(conandata_path, "w") as f:
            yaml.dump({"sources": conandata}, f)


if __name__ == '__main__':
    kwargs = docopt(__doc__, version = '0.1.0')
    main(name = kwargs["<name>"], location = kwargs["<location>"])
