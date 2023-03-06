"""
Copyright 2014  Burkhard Lück <lueck@hube-lueck.de>

Permission to use, copy, modify, and distribute this software
and its documentation for any purpose and without fee is hereby
granted, provided that the above copyright notice appear in all
copies and that both that the copyright notice and this
permission notice and warranty disclaimer appear in supporting
documentation, and that the name of the author not be used in
advertising or publicity pertaining to distribution of the
software without specific, written prior permission.

The author disclaim all warranties with regard to this
software, including all implied warranties of merchantability
and fitness.  In no event shall the author be liable for any
special, indirect or consequential damages or any damages
whatsoever resulting from loss of use, data or profits, whether
in an action of contract, negligence or other tortious action,
arising out of or in connection with the use or performance of
this software.
"""

# This script generates a POT file from a JSON settings file. It
# has been adapted from createjsoncontext.py of KDE's translation
# scripts. It extracts the "label" and "description" values of
# the JSON file using the structure as used by Uranium settings files.

import json
import logging
import time
import collections
from pathlib import Path


def write_setting_text(json_path: Path, destination_path: Path) -> bool:
    """ Writes settings text from json file to pot file. Returns true if a file was written. """
    translation_entries = ""
    with open(json_path, "r", encoding ="utf-8") as data_file:
        setting_dict = json.load(data_file, object_pairs_hook=collections.OrderedDict)

        if "settings" not in setting_dict:
            logging.debug(f"Nothing to translate in file: {setting_dict}")
        else:
            translation_entries = process_settings(json_path.name, setting_dict["settings"])

    if translation_entries:
        output_pot_path = Path(destination_path).joinpath(json_path.name + ".pot")  # Create a pot with a matching filename in the destination path
        with open(output_pot_path, "w", encoding ="utf-8") as output_file:
            output_file.write(create_pot_header())
            output_file.write(translation_entries)
        return True

    return False


def create_translation_entry(file: str, setting: str, field: str, value: str) -> str:
    return "#: {0}\nmsgctxt \"{1} {2}\"\nmsgid \"{3}\"\nmsgstr \"\"\n\n".format(file, setting, field, value.replace("\n", "\\n").replace("\"", "\\\""))


def process_settings(file, settings) -> str:
    translation_entries = ""
    for name, value in settings.items():
        if "label" in value:
            translation_entries += create_translation_entry(file, name, "label", value["label"])

        if "description" in value:
            translation_entries += create_translation_entry(file, name, "description", value["description"])

        if "warning_description" in value:
            translation_entries += create_translation_entry(file, name, "warning_description", value["warning_description"])

        if "error_description" in value:
            translation_entries += create_translation_entry(file, name, "error_description", value["error_description"])

        if "options" in value:
            for item, description in value["options"].items():
                translation_entries += create_translation_entry(file, name, "option {0}".format(item), description)

        if "children" in value:
            translation_entries += process_settings(file, value["children"])

    return translation_entries


def create_pot_header() -> str:
    """ Creates a pot file header """
    header = "#, fuzzy\n"
    header += "msgid \"\"\n"
    header += "msgstr \"\"\n"
    header += "\"Project-Id-Version: Uranium json setting files\\n\"\n"
    header += "\"Report-Msgid-Bugs-To: plugins@ultimaker.com\\n\"\n"
    header += "\"POT-Creation-Date: %s+0000\\n\"\n" %time.strftime("%Y-%m-%d %H:%M")
    header += "\"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n\"\n"
    header += "\"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n\"\n"
    header += "\"Language-Team: LANGUAGE\\n\"\n"
    header += "\"MIME-Version: 1.0\\n\"\n"
    header += "\"Content-Type: text/plain; charset=UTF-8\\n\"\n"
    header += "\"Content-Transfer-Encoding: 8bit\\n\"\n"
    header += "\n"
    return header

