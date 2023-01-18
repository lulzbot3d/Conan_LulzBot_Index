import os
from pathlib import Path

from conan import ConanFile
from conans import tools
from conans.client.subsystems import subsystem_path, deduce_subsystem

from extract_strings import extract_strings_from_project


class ExtractTranslations(object):
    def __init__(self, conanfile: ConanFile):
        self._conanfile = conanfile

    def extract(self, root_path: Path, translations_root_path: Path, translation_template_name: str):
        extract_strings_from_project(root_path, translations_root_path, translation_template_name)

class Pkg(ConanFile):
    name = "translationextractor"
    version = "1.0.0"
    default_user = "ultimaker"
    default_channel = "stable"
    exports = "*"

    def package(self):
        self.copy("*", ".")

    def package_info(self):
        self.cpp_info.set_property("name", "translationextractor")
