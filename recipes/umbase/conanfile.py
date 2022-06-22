from typing import Optional

from conans import ConanFile, tools
from conans.errors import ConanException


class UMBaseConanfile(object):
    """
    Ultimaker base conanfile, for reusing Python code in our repositories
    https://docs.conan.io/en/latest/extending/python_requires.html
    """

    def _um_data(self, recipe_version: Optional[str]) -> dict:
        """
        Extract the version specific data out of a conandata.yml
        """

        if recipe_version:
            if recipe_version in self.conan_data:
                return self.conan_data[recipe_version]

            recipe_version = tools.Version(recipe_version)
            all_versions = []
            for k in self.conan_data:
                try:
                    v = tools.Version(k)
                except ConanException:
                    continue
                all_versions.append(v)
            satifying_versions = sorted([str(v) for v in all_versions if v <= recipe_version])
            if len(satifying_versions) == 0:
                raise ConanException(f"Could not find a maximum satisfying version for {recipe_version} in {all_versions}")
            version = satifying_versions[-1]
            return self.conan_data[version]

        return self.conan_data["None"]


class Pkg(ConanFile):
    name = "umbase"
    version = "0.1.1"
    default_user = "ultimaker"
    default_channel = "stable"
