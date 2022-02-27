import os

from conans import ConanFile, tools
from conans.errors import ConanException


class UltimakerBase(object):
    def ultimaker_layout(self, include_dir = "src"):
        compiler = self.settings.get_safe("compiler")
        multi = compiler in ("Visual Studio", "msvc")

        self.folders.source = "."
        try:
            build_type = str(self.settings.build_type)
        except ConanException:
            raise ConanException("'build_type' setting not defined, it is necessary for cmake_layout()")
        if multi:
            self.folders.build = "build"
        else:
            comp = "" if compiler in ("gcc", "apple-clang") else f"-{compiler}"
            build_type = build_type.lower()
            self.folders.build = f"cmake-build-{build_type}{comp}"
        self.folders.generators = os.path.join(self.folders.build, "conan")
        self.cpp.source.includedirs = [include_dir]
        if multi:
            self.cpp.build.libdirs = [f"{build_type}"]
            self.cpp.build.bindirs = [f"{build_type}"]
        else:
            self.cpp.build.libdirs = ["."]
            self.cpp.build.bindirs = ["."]


class Pkg(ConanFile):
    name = "UltimakerBase"
    version = "0.3"
    default_user = "ultimaker"
    default_channel = "testing"
