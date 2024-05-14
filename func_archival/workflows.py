"""Workflows for managing data pipeline.

preproc_model : Preprocess and model resting EPI data

Notes
-----
EmoRep dependencies:
    func_preprocess>=2.3.0
    func_model>=4.0.0

"""

# %%
import os
import glob
from func_preprocess import workflows as wf_fp
from func_model.workflows import wf_fsl


# %%
def preproc_model(
    subj,
    sess_list,
    proj_dir,
    work_dir,
    log_dir,
    preproc_args,
    model_args,
):
    """Preprocess and model archival resting-state data.

    Wrap workflow methods from func_preprocess and func_model
    to move archival anat and rest EPI data through the same
    pipeline as the Exp2 data. First preprocess data via
    fMRIPrep and FSL methods, then model resting-state data
    via FSL's FEAT.

    Parameters
    ----------
    subj : str
        BIDS subject
    sess_list : list
        BIDS session identifiers
    proj_dir : str, os.PathLike
        Location of project directory
    work_dir : str, os.PathLike
        Location of working directory, for intermediates
    log_dir : str, os.PathLike
        Output location for capturing stdout/err
    preproc_args : dict
        Argument and parameters specific for preprocess method, required
        keys (see also func_preprocess.workflows.run_preproc):
         -  ["fd_thresh"] = framewise displacement threshold
         -  ["ignore_fmaps"] = whether to ignore field maps
    model_args : dict
        Argument and parameters specific for modeling method, required
        keys (see also func_model.workflows.FslFirst):
        -   ["model_name"] = name of FSL model
        -   ["model_level"] = level of FSL model
        -   ["preproc_type"] = preprocessing step used

    Raises
    ------
    KeyError
        Missing required keys in preproc_args or model_args

    """
    # Check for required keys
    preproc_keys = [
        "fd_thresh",
        "ignore_fmaps",
    ]
    for chk_key in preproc_keys:
        if chk_key not in preproc_args.keys():
            raise KeyError(f"Expected key {chk_key} in preproc_args")
    model_keys = [
        "model_name",
        "model_level",
        "preproc_type",
    ]
    for chk_key in model_keys:
        if chk_key not in model_args.keys():
            raise KeyError(f"Expected key {chk_key} in model_args")

    # Setup reference and final directories
    proj_raw = os.path.join(proj_dir, "rawdata")
    proj_deriv = os.path.join(proj_dir, "derivatives")
    proj_pp = os.path.join(proj_deriv, "pre_processing")
    keoki_path = (
        "/mnt/keoki/experiments2/EmoRep/Exp3_Classify_Archival/data_mri_BIDS"
    )

    # Trigger workflows
    chk_path = os.path.join(proj_pp, "fsl_denoise", subj, sess_list[0], "func")
    chk_scale = glob.glob(f"{chk_path}/*scaled_bold.nii.gz")
    if not chk_scale:
        wf_fp.run_preproc(
            subj,
            sess_list,
            proj_raw,
            proj_pp,
            work_dir,
            preproc_args["fd_thresh"],
            preproc_args["ignore_fmaps"],
            log_dir,
            keoki_path=keoki_path,
        )

    wf_obj = wf_fsl.FslFirst(
        subj,
        sess_list[0],
        model_args["model_name"],
        model_args["preproc_type"],
        proj_raw,
        proj_deriv,
        work_dir,
        log_dir,
        keoki_path=keoki_path,
    )
    wf_obj.model_rest()


# %%
