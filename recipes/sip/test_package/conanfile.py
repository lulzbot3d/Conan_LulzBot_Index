from conans import AutoToolsBuildEnvironment, ConanFile, CMake, tools, RunEnvironment
from conans.errors import ConanException
from io import StringIO
import os
import re
import shutil


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        pass


    def test(self):
        pass
