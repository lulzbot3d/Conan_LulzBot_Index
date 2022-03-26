from io import StringIO

from conans import tools
from conan import ConanFile
from conans.errors import ConanException


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "json"

    def test(self):
        python_path = [self.deps_user_info[dep].pythonpath for dep in self.deps_user_info if hasattr(self.deps_user_info[dep], 'pythonpath')]
        path_sep = ";" if self.settings.get_safe("os") == "Windows" else ";"
        buffer = StringIO()
        with tools.environment_append({"PYTHONPATH": path_sep.join(python_path)}):
            try:
                self.run(f"{self.deps_user_info['cpython'].python} -c 'import toml; import pathlib; print(pathlib.Path(toml.__file__).resolve().parent)'", output = buffer)
            except ConanException as e:
                self.output.error(e)
        self.output.info(buffer.getvalue())
