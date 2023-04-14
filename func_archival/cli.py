r"""Run processing workflows for single subject.

Description.

Notes
-----
Requires func_preprocess TODO

Examples
--------
func_archival -e ses-intake -s sub-NA9997

func_archival \
    -e ses-intake \
    -s sub-NA9997 sub-NA9998 \
    --no-freesurfer \
    --fd-thresh 0.2 \
    --ignore-fmaps

"""
# %%
import os
import sys
import time
import textwrap
from datetime import datetime
from argparse import ArgumentParser, RawTextHelpFormatter
from func_archival import submit


# %%
def _get_args():
    """Get and parse arguments."""
    parser = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--ignore-fmaps",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether fmriprep will ignore fmaps,
            True if "--ignore-fmaps" else False.
            """
        ),
    )
    parser.add_argument(
        "--fd-thresh",
        type=float,
        default=0.5,
        help=textwrap.dedent(
            """\
            Framewise displacement threshold
            (default : %(default)s)
            """
        ),
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="rest",
        help=textwrap.dedent(
            """\
            [rest]
            FSL model name, for triggering different workflows
            (default : %(default)s)
            """
        ),
    )
    parser.add_argument(
        "--no-freesurfer",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether to use the --fs-no-reconall option with fmriprep,
            True if "--no--freesurfer" else False.
            """
        ),
    )
    parser.add_argument(
        "--proj-dir",
        type=str,
        default="/hpc/group/labarlab/EmoRep/Exp3_Classify_Archival/data_mri_BIDS",  # noqa: E501
        help=textwrap.dedent(
            """\
            Required when --run-local.
            Path to BIDS-formatted project directory
            (default : %(default)s)
            """
        ),
    )

    required_args = parser.add_argument_group("Required Arguments")
    required_args.add_argument(
        "-e",
        "--session",
        help="MRI session name, e.g. ses-BAS1",
        type=str,
        required=True,
    )
    required_args.add_argument(
        "-s",
        "--subj-list",
        nargs="+",
        help="List of subject IDs to submit for processing",
        type=str,
        required=True,
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return parser


# %%
def main():
    """Setup working environment."""

    # Capture CLI arguments
    args = _get_args().parse_args()
    subj_list = args.sub_list
    sess = args.session
    proj_dir = args.proj_dir
    ignore_fmaps = args.ignore_fmaps
    no_freesurfer = args.no_freesurfer
    fd_thresh = args.fd_thresh
    model_name = args.model_name

    #
    if not os.path.exists(proj_dir):
        raise FileNotFoundError(f"Expected to find directory : {proj_dir}")

    # Get, check environmental vars
    sing_afni = os.environ["SING_AFNI"]
    sing_fmriprep = os.environ["SING_FMRIPREP"]
    fs_license = os.environ["FS_LICENSE"]
    tplflow_dir = os.environ["SINGULARITYENV_TEMPLATEFLOW_HOME"]
    user_name = os.environ["USER"]

    try:
        os.environ["FSLDIR"]
    except KeyError:
        print("Missing required global variable FSLDIR")
        sys.exit(1)

    #
    work_dir = os.path.join("/work", user_name, "EmoRep")
    now_time = datetime.now().strftime("%y-%m-%d_%H:%M")
    # log_dir = os.path.join(
    #     work_dir,
    #     "logs",
    #     f"func_archival_{now_time}",
    # )
    log_dir = os.path.join(
        work_dir,
        "logs",
        "func_archival_test",
    )
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    #
    preproc_args = {
        "sing_fmriprep": sing_fmriprep,
        "tplflow_dir": tplflow_dir,
        "fs_license": fs_license,
        "fd_thresh": fd_thresh,
        "ignore_fmaps": ignore_fmaps,
        "no_freesurfer": no_freesurfer,
        "sing_afni": sing_afni,
    }
    model_args = {"model_name": model_name}

    #
    for subj in subj_list:
        sched_wf = submit.ScheduleWorkflow(
            subj, sess, proj_dir, work_dir, log_dir, user_name
        )
        sched_wf.omnibus(preproc_args, model_args)
        sched_wf.submit()
        time.sleep(3)


if __name__ == "__main__":

    # Require proj env
    # TODO require DCC env
    env_found = [x for x in sys.path if "emorep" in x]
    if not env_found:
        print("\nERROR: missing required project environment 'emorep'.")
        print("\tHint: $labar_env emorep\n")
        sys.exit(1)
    main()
