
from typing import Optional

from conans import ConanFile

from semver import max_satisfying


class UMBaseConanfile(object):
    """
    Ultimaker base conanfile, for reusing Python code in our repositories
    https://docs.conan.io/en/latest/extending/python_requires.html
    """

    def _um_data(self, recipe_version: Optional[str]) -> dict:
        """
        Extract the version specific data out of a conandata.yml
        """

        all_versions = set()
        if recipe_version:
            for vers in self.conan_data.values():
                for v in vers:
                    all_versions.add(v)
            all_versions.remove("None")
            version = max_satisfying(all_versions, recipe_version, loose = True, include_prerelease = False)
            if version is None:
                version = "None"
        else:
            version = "None"

        data = {}
        for k, ver in self.conan_data.items():
            data[k] = ver[version]
        return data


class Pkg(ConanFile):
    name = "umbase"
    version = "0.1"
    default_user = "ultimaker"
    default_channel = "stable"
