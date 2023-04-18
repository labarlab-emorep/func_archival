"""Workflows for managing data pipeline."""
# %%
import os
import glob
from func_preprocess import workflows as wf_fp
from func_model import workflows as wf_fm


# %%
def preproc_model(
    subj,
    sess,
    proj_dir,
    work_dir,
    log_dir,
    preproc_args,
    model_args,
):
    """Coordinate worklow methods.

    Conduct entire process workflow by coordinating step-specific
    workflows. This method triggers the following steps:
        -   preprocess
        -   model
        -   target_id

    Parameters
    ----------
    subj : str
        BIDS subject
    sess : str
        BIDS session
    proj_dir : str, os.PathLike
        Location of project directory
    work_dir : str, os.PathLike
        Location of working directory, for intermediates
    log_dir : str, os.PathLike
        Output location for capturing stdout/err
    preproc_args : dict
        Argument and parameter specific for preprocess method,
        requires keys that match preprocess keywords (see also
        help(workflows.preprocess)):
         -  ["sing_fmriprep"] = location of fmriprep.simg
         -  ["tplflow_dir"] = location of templateflow directory
         -  ["fs_license"] = location of Freesurfer license
         -  ["fd_thresh"] = framewise displacement threshold
         -  ["ignore_fmaps"] = whether to ignore field maps
         -  ["no_freesurfer"] = whether to turn off Freesrufer
         -  ["sing_afni"] = location of afni.simg
    model_args : dict
        Same as preproc_args, but for workflows.model.
        -   ["model_name"] = name of FSL model
        -   ["model_level"] = level of FSL model

    """
    # Check for required keys
    preproc_keys = [
        "sing_fmriprep",
        "tplflow_dir",
        "fs_license",
        "fd_thresh",
        "ignore_fmaps",
        "no_freesurfer",
        "sing_afni",
    ]
    for chk_key in preproc_keys:
        if chk_key not in preproc_args.keys():
            raise KeyError(f"Expected key {chk_key} in preproc_args")
    model_keys = ["model_name", "model_level"]
    for chk_key in model_keys:
        if chk_key not in model_args.keys():
            raise KeyError(f"Expected key {chk_key} in model_args")

    # Setup reference and final directories
    proj_raw = os.path.join(proj_dir, "rawdata")
    proj_deriv = os.path.join(proj_dir, "derivatives")
    proj_pp = os.path.join(proj_deriv, "pre_processing")

    # Trigger workflows
    chk_path = os.path.join(proj_pp, "fsl_denoise", subj, sess, "func")
    chk_scale = glob.glob(f"{chk_path}/*scaled_bold.nii.gz")
    if not chk_scale:
        wf_fp.run_preproc(
            subj,
            proj_raw,
            proj_pp,
            os.path.join(work_dir, "pre_processing"),
            preproc_args["sing_fmriprep"],
            preproc_args["tplflow_dir"],
            preproc_args["fs_license"],
            preproc_args["fd_thresh"],
            preproc_args["ignore_fmaps"],
            preproc_args["no_freesurfer"],
            preproc_args["sing_afni"],
            log_dir,
            False,
        )

    wf_fsl = wf_fm.FslFirst(
        subj,
        sess,
        model_args["model_name"],
        model_args["model_level"],
        proj_raw,
        proj_deriv,
        work_dir,
        log_dir,
    )
    wf_fsl.model_rest()
