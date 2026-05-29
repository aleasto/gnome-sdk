#!/usr/bin/env python3

import os
import sys
import yaml

config_file = "snapcraft.yaml"
if not os.path.exists(config_file):
    config_file = os.path.join("snap", "snapcraft.yaml")

if len(sys.argv) > 1:
    config_file = sys.argv[1]

data = yaml.safe_load(open(config_file, "r"))

########################################################
# Ensure that "deb" part depends on all previous parts #
########################################################

deb_exceptions = ['buildenv']

def filldeps(part):
    """ Fill recursively the dependencies of each part """
    global data
    output = []
    if 'after' in data['parts'][part]:
        for dep in data['parts'][part]['after']:
            # it's not a problem to have duplicated dependencies
            output += filldeps(dep)
            output.append(dep)
    return output

dependencies = {}

# get the dependencies for each part
for part in data["parts"]:
    dependencies[part] = filldeps(part)

deb_dependencies = []
for part in data["parts"]:
    if "debs" == part:
        continue
    if "debs" in dependencies[part]:
        # if it depends on debs, it must be after, so don't take it into account
        continue
    if part in deb_exceptions:
        continue
    deb_dependencies.append(part)

failed = False
for dependency in deb_dependencies:
    if dependency not in dependencies["debs"]:
        print(f"DEBS part must be after {dependency}")
        failed = True

def check_dependency(*, part_name, part, strings_to_find, dependency):
    if "meson-parameters" not in part:
        return False
    for meson_parameter in part["meson-parameters"]:
        for string_to_find in strings_to_find:
            if (meson_parameter.find(string_to_find) != -1) and (dependency not in part["after"]):
                print(f"Part {part_name} requires {dependency} dependency due to meson option {meson_parameter}")
                return True
    return False

###################################################
# Ensure that any part that builds introspection, #
# depends on gobject-introspection.               #
###################################################

goi_exceptions = ["glib"] # parts that must NOT have gobject-introspection as dependency, even if detected automatically
for part_name in data["parts"]:
    if part_name in goi_exceptions:
        continue
    if check_dependency(part_name=part_name,
                        part = data["parts"][part_name],
                        strings_to_find=["introspection"],
                        dependency="gobject-introspection"):
        failed = True

###############################################
# Ensure that any part that builds VAPI info, #
# depends on vala.                            #
###############################################

vapi_exceptions = ['vala'] # parts that must NOT have vala as dependency, even if detected automatically
for part_name in data["parts"]:
    if part_name in vapi_exceptions:
        continue
    if check_dependency(part_name=part_name,
                        part = data["parts"][part_name],
                        strings_to_find=['vala', 'vapi'],
                        dependency="vala"):
        failed = True

###########################################################
# Ensure that all parts have build-environment: *buildenv #
###########################################################

build_exceptions = ['buildenv', 'buildtool', 'python-build-deps', 'ninja', 'meson-deps', 'libtool', 'pangomm', 'atkmm', 'gtkmm', 'debs', 'bindtextdomain', 'cleanup']
expected_buildenv = data["parts"]["buildenv"]["build-environment"]
for part_name in data["parts"]:
    if part_name == "buildenv":
        continue
    if part_name in build_exceptions:
        if "build-environment" in data["parts"][part_name] and data["parts"][part_name]["build-environment"] == expected_buildenv:
            print(f"Part {part_name} seems to have the same build-environment as buildenv. Please check if it is correct.")
            failed = True
        continue
    if "build-environment" not in data["parts"][part_name] or data["parts"][part_name]["build-environment"] != expected_buildenv:
        print(f"Part {part_name} must have build-environment: *buildenv")
        failed = True

if failed:
    sys.exit(1)
print("All dependencies are correct")
