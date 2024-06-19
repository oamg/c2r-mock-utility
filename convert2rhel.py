#!/usr/bin/python2
import json
import os
import subprocess
import sys
import time

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
ANALYZE_NO_ISSUE_FILE = "/usr/share/convert2rhel/data/analyze/convert2rhel-pre-conversion.json"
ANALYZE_KMOD_INHIBITOR_FILE = "/usr/share/convert2rhel/data/kmod/convert2rhel-pre-conversion.json"
CONVERT_NO_ISSUE_FILE = "/usr/share/convert2rhel/data/convert/convert2rhel-post-conversion.json"
C2R_LOG_FOLDER = "/var/log/convert2rhel"
C2R_ANALYZE_JSON_LOG_LOCATION = C2R_LOG_FOLDER + "/convert2rhel-pre-conversion.json"
C2R_CONVERT_JSON_LOG_LOCATION = C2R_LOG_FOLDER + "/convert2rhel-post-conversion.json"


def create_log_folder():
    """Create a c2r log folder if does not exists"""
    if not os.path.exists(C2R_LOG_FOLDER):
        os.makedirs(C2R_LOG_FOLDER)


def create_report(reportfile, log_destination_location):
    """
    Download and put the c2r report file in the log directory
    where the rhc-worker-script parse the result of the c2r run
    """
    create_log_folder()
    cmd = ["cp", reportfile, log_destination_location]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    output = ""
    for line in iter(process.stdout.readline, b""):
        line = line.decode("utf8")
        output += line

    # Wait for the process to end
    process.wait()

    if process.returncode != 0:
        print(output)
        raise RuntimeError("Mock failed to create a report")


def main():
    """Main script logic"""

    script_es = 0

    if SCRIPT_MODE not in ("ANALYSIS", "CONVERSION"):
        print("SCRIPT_MODE envar is not one of the expected, got: {}".format(SCRIPT_MODE))
        sys.exit(10)

    # Decide what to do based on existence of a specific file.
    # This serves as a communication with a running test.
    if os.path.isfile(MOCK_DUMP_ENV_VARS):
        with open(MOCK_OUTPUT_FILE, mode="w") as f:
            json.dump(dict(os.environ), f)

        if SCRIPT_MODE == "ANALYSIS":
            create_report(ANALYZE_NO_ISSUE_FILE, C2R_ANALYZE_JSON_LOG_LOCATION)
        else:
            create_report(CONVERT_NO_ISSUE_FILE, C2R_CONVERT_JSON_LOG_LOCATION)

    elif os.path.isfile(MOCK_INFINITE_LOOP):
        while True:
            # Infinitely sleep and write every 5 seconds actual time.
            time.sleep(5)
            with open(C2R_LOG_FOLDER + "/convert2rhel.log", mode="a") as f:
                f.write(time.ctime() + "\n")

    elif os.path.isfile(MOCK_KMOD_INHIBITOR):
        create_report(ANALYZE_KMOD_INHIBITOR_FILE, C2R_ANALYZE_JSON_LOG_LOCATION)

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

        # If the script finishes successfully create a report
        if process.returncode == 0:
            if SCRIPT_MODE == "ANALYSIS":
                create_report(ANALYZE_NO_ISSUE_FILE, C2R_ANALYZE_JSON_LOG_LOCATION)
            else:
                create_report(CONVERT_NO_ISSUE_FILE, C2R_CONVERT_JSON_LOG_LOCATION)

        # Exit with the executed script return code
        script_es = process.returncode

    elif os.path.isfile(MOCK_DO_NOTHING):
        if SCRIPT_MODE == "ANALYSIS":
            create_report(ANALYZE_NO_ISSUE_FILE, C2R_ANALYZE_JSON_LOG_LOCATION)
        else:
            create_report(CONVERT_NO_ISSUE_FILE, C2R_CONVERT_JSON_LOG_LOCATION)

    else:
        print(
            "Script do now know what to do.. :(\n \
             create one of the specific files to tell it what to do."
        )
        sys.exit(10)

    sys.exit(script_es)


if __name__ == "__main__":
    main()
