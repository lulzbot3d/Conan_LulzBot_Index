from os import path

from conan import ConanFile
from conan.tools.files import copy


class Pkg(ConanFile):
    name = "standardprojectsettings"
    version = "0.1.1"
    default_user = "ultimaker"
    default_channel = "stable"
    exports_sources = "StandardProjectSettings.cmake"
    package_type = "build-scripts"

    def package(self):
        copy(self, "StandardProjectSettings.cmake", src = self.export_sources_folder, dst = path.join(self.package_folder, "res", "cmake"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []

        self.cpp_info.set_property("name", "standardprojectsettings")
        self.cpp_info.set_property("cmake_build_modules", [path.join("res", "cmake", "StandardProjectSettings.cmake")])
