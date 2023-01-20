from pathlib import Path
from conan import ConanFile

from extract_strings import TranslationExtractor


class ExtractTranslations(object):
    def __init__(self, conanfile: ConanFile, translations_root_path: Path, translation_template_name: str):
        self._conanfile = conanfile
        self.translations_root_path = translations_root_path
        self.translation_template_name = translation_template_name

    def generate(self):
        gettext_path = self._conanfile.dependencies["gettext"].cpp_info.bindirs[0]
        extractor = TranslationExtractor(self._conanfile.source_path, self.translations_root_path, self.translation_template_name, gettext_path)
        extractor.extract_strings_to_pot_files()
        extractor.update_po_files_all_languages()


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
