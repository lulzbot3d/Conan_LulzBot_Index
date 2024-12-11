from conan import ConanFile

from pathlib import Path

required_conan_version = ">=2.7.0"


def sanitize_version(version):
        # npm will otherwise 'sanitize' the version number
        return version.replace("+", "-")


def conf_package_json(conanfile: ConanFile, **kwargs):
    entry_point = [p.name for p in Path(conanfile.package_folder, "bin").rglob("*.js")][0]
    package_json = {
        "name": f"@{conanfile.author.lower()}/{conanfile.name.lower()}js",
        "version": f"{sanitize_version(conanfile.version)}",
        "description": f"JavaScript / TypeScript bindings for {conanfile.name}, a {conanfile.description}",
        "main": f"bin/{entry_point}",
        "repository": {
            "type": "git",
            "url": conanfile.url
        },
        "author": conanfile.author,
        "license": conanfile.license,
        "keywords": conanfile.topics,
        "files": [
            "bin",
            "package.json"
        ]
    }
    package_json |= kwargs
    conanfile.output.info(f"Generated package.json: {package_json}")

    conanfile.conf_info.define(f"user.{conanfile.name.lower()}:package_json", package_json)


class PyReq(ConanFile):
    name = "npmpackage"
    description = "This is a base conan file description for C++ libraries/applications that use the npm generator"
    package_type = "python-require"
