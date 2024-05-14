r"""Run processing workflows for single subject.

Move archival data through preprocessing and FSL modeling. Wraps
methods used for Exp2_Compute_Emotion.

Example
-------
func_archival -s sub-08326
func_archival \
    -s sub-08326 \
    --preproc-type smoothed

"""

# %%
import os
import sys
import time
import textwrap
from datetime import datetime
from argparse import ArgumentParser, RawTextHelpFormatter
from func_archival import submit
import func_archival._version as ver


# %%
def _get_args():
    """Get and parse arguments."""
    ver_info = f"\nVersion : {ver.__version__}\n\n"
    parser = ArgumentParser(
        description=ver_info + __doc__, formatter_class=RawTextHelpFormatter
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
        "--sessions",
        nargs="+",
        default=["ses-BAS1"],
        choices=["ses-BAS1"],
        help=textwrap.dedent(
            """\
            List of BIDS session identifiers
            (default : %(default)s)
            """
        ),
    )
    parser.add_argument(
        "--preproc-type",
        type=str,
        default="scaled",
        choices=["scaled", "smoothed"],
        help=textwrap.dedent(
            """\
            Determine whether to use scaled or smoothed preprocessed EPIs
            (default : %(default)s)
            """
        ),
    )
    parser.add_argument(
        "--proj-dir",
        type=str,
        default="/hpc/group/labarlab/EmoRep/Exp3_Classify_Archival/data_mri_BIDS",  # noqa: E501
        help=textwrap.dedent(
            """\
            Path to BIDS-formatted project directory
            (default : %(default)s)
            """
        ),
    )

    required_args = parser.add_argument_group("Required Arguments")
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
    subj_list = args.subj_list
    sess_list = args.sessions
    proj_dir = args.proj_dir
    ignore_fmaps = args.ignore_fmaps
    fd_thresh = args.fd_thresh
    preproc_type = args.preproc_type

    # Setup work, log directories
    work_dir = os.path.join("/work", os.environ["USER"], "Archival")
    now_time = datetime.now().strftime("%y%m%d_%H%M")
    log_dir = os.path.join(
        work_dir,
        "logs",
        f"func_archival_{now_time}",
    )
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Build pipeline-step arguments
    preproc_args = {
        "fd_thresh": fd_thresh,
        "ignore_fmaps": ignore_fmaps,
    }
    model_args = {
        "model_name": "rest",
        "model_level": "first",
        "preproc_type": preproc_type,
    }

    # Submit workflows
    for subj in subj_list:
        sched_wf = submit.ScheduleWorkflow(
            subj, sess_list, proj_dir, work_dir, log_dir
        )
        sched_wf.run_all(preproc_args, model_args)
        sched_wf.submit()
        time.sleep(3)


if __name__ == "__main__":

    # Require proj env
    env_found = [x for x in sys.path if "emorep" in x]
    if not env_found:
        print("\nERROR: missing required project environment 'emorep'.")
        print("\tHint: $labar_env emorep\n")
        sys.exit(1)
    main()
