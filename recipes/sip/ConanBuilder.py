from sipbuild import SetuptoolsBuilder


class ConanBuilder(SetuptoolsBuilder):
    def __init__(self, project, **kwargs):
        print("Using the Conan builder")
        super(ConanBuilder, self).__init__(project, **kwargs)

    def build(self):
        """ Build the project in-situ. """
        print("Generating the source files")
        self._generate_bindings()
        self._generate_scripts()
