#!/usr/bin/python2
import json
import os
import subprocess
import sys
import time
import argparse

# Based on the existence of the following files do a certain thing
MOCK_DUMP_ENV_VARS = "/tmp/c2r_mock_dump_env_vars"  # Dump env vars
MOCK_INFINITE_LOOP = "/tmp/c2r_mock_infinite_loop"  # Infinitely loop
MOCK_KMOD_INHIBITOR = "/tmp/c2r_mock_kmod_inhibitor"  # Report an inhibitor about unsupported kernel modules
MOCK_EXECUTE_SCRIPT = "/tmp/c2r_mock_execute_script"  # Do whatever is inside this script file
MOCK_DO_NOTHING = "/tmp/c2r_mock_do_nothing"  # Do nothing, just create a report and end immediately


# The output of a mock to check the test result
MOCK_OUTPUT_FILE = "/tmp/c2r_mock_test.json"

# Script mode as defined in the script
# (https://github.com/oamg/convert2rhel-insights-tasks/blob/main/scripts/c2r_script.py#L15)
SCRIPT_MODE = os.environ.get("SCRIPT_MODE", None)

# Report json files as expected by script
BASE_REPORT_DATA_FOLDER = "/usr/share/convert2rhel/data/"
ANALYZE_NO_ISSUE_FILE = BASE_REPORT_DATA_FOLDER + "analyze/convert2rhel-pre-conversion.json"
ANALYZE_KMOD_INHIBITOR_FILE = BASE_REPORT_DATA_FOLDER + "kmod/convert2rhel-pre-conversion.json"
CONVERT_NO_ISSUE_FILE = BASE_REPORT_DATA_FOLDER + "convert/convert2rhel-post-conversion.json"
C2R_LOG_FOLDER = "/var/log/convert2rhel"
C2R_ANALYZE_JSON_LOG_LOCATION = C2R_LOG_FOLDER + "/convert2rhel-pre-conversion.json"
C2R_CONVERT_JSON_LOG_LOCATION = C2R_LOG_FOLDER + "/convert2rhel-post-conversion.json"

REPORT_STATUS_ORDER = ["SUCCESS", "INFO", "SKIP", "OVERRIDABLE", "WARNING", "ERROR"]


def parse_arguments(args):
    parser = argparse.ArgumentParser()

    # Add allowed options
    parser.add_argument(
        "-y",
        action='store_true'
    )
    parser.add_argument(
        "--els",
        action='store_true'
    )

    # Parse arguments
    return parser.parse_args(args)


def create_log_folder():
    """Create a c2r log folder if does not exists"""
    os.makedirs(
        name=C2R_LOG_FOLDER,
        exist_ok=True
    )


def create_report(reportfile, log_destination_location):
    """
    Download and put the c2r report file in the log directory
    where the rhc-worker-script parse the result of the c2r run
    """
    create_log_folder()
    try:
        with open(log_destination_location, "w") as f:
            f.write(json.dumps(reportfile))
    except:
        raise RuntimeError("Mock failed to create a report")


'''
    Crafts a report adding all entries from :path_issues to the
    base reportfile located in :reportfile_path

    :param reportfile_path: Path to the base reportfile
    :param report_issues: Dict with the paths to the reportfiles to add
                        Dict has to be str -> str.
'''
def craft_report(reportfile_path, report_issues):
    BASE_REPORT_CRAFT_FOLDER = BASE_REPORT_DATA_FOLDER + "craft/"

    reportfile = {}

    # Get the base reportfile
    with open(reportfile_path, mode="r") as f:
        reportfile = json.load(f)

    # Push all report_issues into base reportfile
    for report_issue in report_issues.values():
        REPORT_CRAFT_FOLDER = BASE_REPORT_CRAFT_FOLDER + report_issue

        with open(REPORT_CRAFT_FOLDER + ".json", mode="r") as f:
            json_issue = json.load(f)

        if REPORT_STATUS_ORDER.index(json_issue["status"]) > REPORT_STATUS_ORDER.index(reportfile["status"]):
            reportfile["status"] = json_issue["status"]

        for action_key in json_issue["actions"].keys():
            reportfile["actions"][action_key] = json_issue["actions"][action_key]

    return reportfile


def main():
    """Main script logic"""

    script_es = 0
    reportfile_path = ""
    log_destination_location = ""
    report_issues = {}

    if SCRIPT_MODE not in ("ANALYSIS", "CONVERSION"):
        print("SCRIPT_MODE envar is not one of the expected, got: {}".format(SCRIPT_MODE))
        sys.exit(10)

    # Set defaults
    if SCRIPT_MODE == "ANALYSIS":
        reportfile_path = ANALYZE_NO_ISSUE_FILE
        log_destination_location = C2R_ANALYZE_JSON_LOG_LOCATION
    else:
        reportfile_path = CONVERT_NO_ISSUE_FILE
        log_destination_location = C2R_CONVERT_JSON_LOG_LOCATION

    # Parse arguments
    parsed_opts = parse_arguments(sys.argv[2:])
    
    if not parsed_opts.els and SCRIPT_MODE == "ANALYSIS":
        report_issues["els"] = "els"
    
    if not parsed_opts.y:
        print("Missing parameter: \"-y\".")
        sys.exit(10)

    # Decide what to do based on existence of a specific file.
    # This serves as a communication with a running test.
    if os.path.isfile(MOCK_DUMP_ENV_VARS):
        with open(MOCK_OUTPUT_FILE, mode="w") as f:
            json.dump(dict(os.environ), f)

    elif os.path.isfile(MOCK_INFINITE_LOOP):
        while True:
            # Infinitely sleep and write every 5 seconds actual time.
            time.sleep(5)
            with open(C2R_LOG_FOLDER + "/convert2rhel.log", mode="a") as f:
                f.write(time.ctime() + "\n")

    elif os.path.isfile(MOCK_KMOD_INHIBITOR):
        report_issues["KMOD"] = "kmod"

        if SCRIPT_MODE == "CONVERSION":
            script_es = 1

    elif os.path.isfile(MOCK_EXECUTE_SCRIPT):
        # Check if file is executable
        cmd = ["[", "-x", MOCK_EXECUTE_SCRIPT, "]"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        process.wait()

        if process.returncode != 0:
            print("The script is not executable, make it executable to run!")
            sys.exit(10)

        # Execute the MOCK_EXECUTE_SCRIPT file path
        process = subprocess.Popen(MOCK_EXECUTE_SCRIPT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        # Wait for the process to end
        process.wait()

        # Exit with the executed script return code
        script_es = process.returncode

    elif os.path.isfile(MOCK_DO_NOTHING):
        pass

    else:
        print(
            "Script do now know what to do.. :(\n \
             create one of the specific files to tell it what to do."
        )
        sys.exit(10)

    reportfile = craft_report(reportfile_path, report_issues)
    create_report(reportfile, log_destination_location)

    sys.exit(script_es)


if __name__ == "__main__":
    main()
