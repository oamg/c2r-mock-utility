#!/usr/bin/python2
import os
import subprocess
import sys

DUMP_ENV_VARS = "/tmp/c2r_mock_dump_env_vars"
MOCK_OUTPUT_FILE = "/tmp/c2r_mock_test.out"
SCRIPT_MODE = os.environ.get("SCRIPT_MODE", None)

ANALYZE_NO_ISSUE_FILE_URL = "/usr/share/convert2rhel/data/convert2rhel-pre-conversion.json"
C2R_LOG_FOLDER = "/var/log/convert2rhel"
C2R_PRE_CONVERSION_JSON_LOG_LOCATION = C2R_LOG_FOLDER + "/convert2rhel-pre-conversion.json"


def create_log_folder():
    """Create a c2r log folder if does not exists"""
    if not os.path.exists(C2R_LOG_FOLDER):
        os.makedirs(C2R_LOG_FOLDER)


def create_successful_report():
    """
    Download and put the c2r report file in the log directory
    where the rhc-worker-script parse the result of the c2r run
    """
    create_log_folder()
    if SCRIPT_MODE == "ANALYSIS":
        cmd = ["copy", ANALYZE_NO_ISSUE_FILE_URL, C2R_PRE_CONVERSION_JSON_LOG_LOCATION]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        output = ""
        for line in iter(process.stdout.readline, b""):
            line = line.decode("utf8")
            output += line

        # Wait for the process to end
        process.wait()

        return output, process.returncode


def main():
    """Main script logic"""

    if SCRIPT_MODE not in ("ANALYSIS", "CONVERSION"):
        print("SCRIPT_MODE envar is not one of the expected, got: {}".format(SCRIPT_MODE))
        sys.exit(10)

    # Decide what to do based on existence of a specific file.
    # This serves as a communication with a running test.
    if os.path.isfile(DUMP_ENV_VARS):
        with open(MOCK_OUTPUT_FILE, mode="w") as f:
            f.write(str(os.environ) + "\n")

        output, return_code = create_successful_report()
        if return_code != 0:
            print(output)
    else:
        print(
            "Script do now know what to do.. :( \
             create one of the specific files to tell it what to do."
        )
        sys.exit(10)


if __name__ == "__main__":
    main()
