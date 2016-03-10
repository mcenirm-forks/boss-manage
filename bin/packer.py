#!/usr/bin/env python3

import argparse
import sys
import os
import glob
import shlex
import subprocess
from distutils.spawn import find_executable

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ["PATH"] += ":" + os.path.join(REPO_ROOT, "bin")

# packer.sh config [, config [,...]]
# config is the name of a file in packer/variables/ or all
#   - change this to just use the top level definitions in top.sls?
# --single-thread only builds one at a time (default is all at once)
# --name= give a name to the build, defaults start of the commit hash
# --only= the packer config section to build, defaults amazon-ebs
# --no-bastion don't use aws-bastion, defaults to true

def get_commit():
    cmd = "git rev-parse HEAD"
    result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8").strip()

def execute(cmd, output_file):
    return subprocess.Popen(shlex.split(cmd), stderr=subprocess.STDOUT, stdout=open(output_file, "w"))

if __name__ == '__main__':
    for cmd in ("git", "packer"):
        if find_executable(cmd) is None:
            print("Could not locate {} binary on the system, required...".format(cmd))
            sys.exit(1)

    git_hash = get_commit()

    def create_help(header, options):
        """Create formated help."""
        return "\n" + header + "\n" + \
               "\n".join(map(lambda x: "  " + x, options)) + "\n"

    config_glob = os.path.join(REPO_ROOT, "packer", "variables", "*")
    config_names = [x.split(os.path.sep)[-1] for x in glob.glob(config_glob)]
    config_help_names = list(config_names)
    config_help_names.append("all")
    config_help = create_help("config is on of the following:", config_help_names)

    parser = argparse.ArgumentParser(description = "Script the building of machines images using Packer and SaltStack",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=config_help)
    parser.add_argument("--single-thread",
                        action = "store_true",
                        default = False,
                        help = "Only build one config at a time. (default: Build all configs at the same time)")
    parser.add_argument("--only",
                        metavar = "<packer-builder>",
                        default = "amazon-ebs",
                        help = "Which Packer building to use. (default: amazon-ebs)")
    parser.add_argument("--name",
                        metavar = "<build name>",
                        default = git_hash[:8],
                        help = "The build name for the machine image(s). (default: First 8 characters of the git SHA1 hash)")
    parser.add_argument("--no-bastion",
                        action = "store_false",
                        default = True,
                        dest="bastion",
                        help = "Don't use the aws-bastion file when building. (default: Use the bastion)")
    parser.add_argument("config",
                        choices = config_help_names,
                        metavar = "<config>",
                        nargs = "+",
                        help="Packer variable to build a machine image for")

    args = parser.parse_args()

    if "all" in args.config:
        args.config = config_names

    bastion_config = "-var-file=" + os.path.join(REPO_ROOT, "config", "aws-bastion")
    credentials_config = os.path.join(REPO_ROOT, "config", "aws-credentials")
    packer_file = os.path.join(REPO_ROOT, "packer", "vm.packer")

    if not os.path.exists(credentials_config):
        print("Could not locate AWS credentials file at '{}', required...".format(credentials_config))
        sys.exit(1)

    packer_logs = os.path.join(REPO_ROOT, "packer", "logs")
    if not os.path.isdir(packer_logs):
        os.mkdir(packer_logs)

    cmd = """{packer} build
             {bastion} -var-file={credentials}
             -var-file={machine} -var 'name_suffix={name}'
             -var 'commit={commit}' -var 'force_deregister={deregister}'
             -only={only} {packer_file}"""
    cmd_args = {
        "packer" : "packer",
        "bastion" : bastion_config if args.bastion else "",
        "credentials" : credentials_config,
        "only" : args.only,
        "packer_file" : packer_file,
        "name" : "-" + args.name,
        "commit" : git_hash,
        "deregister" : "true" if args.name == "test" else "false",
        "machine" : "" # replace for each call
    }

    procs = []
    for config in args.config:
        print("Launching {} configuration".format(config))
        log_file = os.path.join(packer_logs, config + ".log")
        cmd_args["machine"] = os.path.join(REPO_ROOT, "packer", "variables", config)
        proc = execute(cmd.format(**cmd_args), log_file)

        if args.single_thread:
            print("Waiting for build to finish")
            proc.wait()
        else:
            procs.append(proc)

    try:
        print("Waiting for all builds started to finish")
        for proc in procs:
            proc.wait()
    except KeyboardInterrupt: # <CTRL> + c
        print("Killing builds")
        for proc in procs:
            proc.poll()
            if proc.returncode is None:
                proc.kill()