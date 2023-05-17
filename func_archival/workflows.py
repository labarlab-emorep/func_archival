"""Workflows for managing data pipeline.

preproc_model : Preprocess and model resting EPI data

Notes
-----
Requires func_preprocess and func_model.

"""
# %%
import os
import glob
from func_preprocess import workflows as wf_fp
from func_model import workflows as wf_fm


# %%
def preproc_model(
    subj,
    sess_list,
    proj_dir,
    work_dir,
    log_dir,
    user_name,
    rsa_key,
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
    user_name : str, optional
        User name for DCC, labarserv2
    rsa_key : str, os.PathLike, optional
        Location of RSA key for labarserv2
    preproc_args : dict
        Argument and parameters specific for preprocess method, required
        keys (see also func_preprocess.workflows.run_preproc):
         -  ["sing_fmriprep"] = location of fmriprep.simg
         -  ["tplflow_dir"] = location of templateflow directory
         -  ["fs_license"] = location of Freesurfer license
         -  ["fd_thresh"] = framewise displacement threshold
         -  ["ignore_fmaps"] = whether to ignore field maps
         -  ["sing_afni"] = location of afni.simg
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
        "sing_fmriprep",
        "tplflow_dir",
        "fs_license",
        "fd_thresh",
        "ignore_fmaps",
        "sing_afni",
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
            os.path.join(work_dir, "pre_processing"),
            preproc_args["sing_fmriprep"],
            preproc_args["tplflow_dir"],
            preproc_args["fs_license"],
            preproc_args["fd_thresh"],
            preproc_args["ignore_fmaps"],
            preproc_args["sing_afni"],
            log_dir,
            False,
            user_name,
            rsa_key,
            keoki_path,
        )

    wf_fsl = wf_fm.FslFirst(
        subj,
        sess_list[0],
        model_args["model_name"],
        model_args["model_level"],
        model_args["preproc_type"],
        proj_raw,
        proj_deriv,
        work_dir,
        log_dir,
        user_name,
        rsa_key,
        keoki_path,
    )
    wf_fsl.model_rest()


# %%
