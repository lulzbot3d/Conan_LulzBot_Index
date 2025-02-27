import os
from pathlib import Path

from conan import ConanFile

required_conan_version = ">=2.7.0"


def sanitize_version(version):
    # npm will otherwise 'sanitize' the version number
    return version.replace("+", "-")


def generate_package_json(conanfile: ConanFile, entry_point, **kwargs):
    package_json = {
        "name": f"@lulzbot3d/{conanfile.name.lower()}js",
        "version": f"{sanitize_version(conanfile.version)}",
        "description": f"JavaScript / TypeScript bindings for {conanfile.name}, a {conanfile.description}",
        "main": entry_point,
        "repository": {
            "type": "git",
            "url": conanfile.url
        },
        "author": "LulzBot",
        "license": conanfile.license,
        "keywords": conanfile.topics,
        "files": [
            str(Path(entry_point).parent),
            "package.json"
        ]
    }
    package_json |= kwargs
    return package_json


def conf_package_json(conanfile: ConanFile, **kwargs):
    package_json = generate_package_json(conanfile,
                                         os.path.join(conanfile.cpp.package.bindirs[0], conanfile.cpp.package.bin[0]),
                                         **kwargs)
    conanfile.conf_info.define(f"user.{conanfile.name.lower()}:package_json", package_json)


class PyReq(ConanFile):
    name = "npmpackage"
    description = "This is a base conan file description for C++ libraries/applications that use the npm generator"
    package_type = "python-require"
