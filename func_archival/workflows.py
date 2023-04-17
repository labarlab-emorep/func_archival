"""Workflows for managing data pipeline.

preprocess  : conduct preprocessing on EPI data via fMRIPrep and FSL
model       : TODO
omnibus     : run all workflows in their respective order

"""
# %%
import os
import glob
from func_preprocess import preprocess as pp


# %%
def run_preprocess(
    subj,
    sess,
    proj_dir,
    work_dir,
    log_dir,
    user_name,
    sing_fmriprep,
    tplflow_dir,
    fs_license,
    fd_thresh,
    ignore_fmaps,
    no_freesurfer,
    sing_afni,
):
    """Preprocess EPI data via fMRIPrep and FSL.

    Conduct the following preprocessing for all runs
    of EPI data:
        -   fMRIPrep, yielding output in both anat and
                MNI152NLin6Asym res-2 space
        -   Bandpass filtering
        -   Masking
        -   Scaling by 10000/median

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
    user_name : str
        DCC login user name
    sing_fmriprep : str, os.PathLike
        Location and image of fmriprep singularity file
    tplflow_dir : str, os.PathLike
        Clone location of templateflow
    fs_license : str, os.PathLike
        Location of FreeSurfer license
    fd_thresh : float
        Threshold for framewise displacement
    ignore_fmaps : bool
        Whether to incorporate fmaps in preprocessing
    no_freesurfer : bool
        Whether to use the --fs-no-reconall option
    sing_afni : str, os.PathLike
        Location of afni singularity image

    Returns
    -------
    dict
        Paths to files relevant for workflows.model
        "preproc_bold": ["/paths/to/*preproc_bold.nii.gz"]
        "mask_bold": ["/paths/to/*desc-brain_mask.nii.gz"]
        "mask_anat": ["/path/to/anat/*desc-brain_mask.nii.gz"]
        "scaled_preproc": ["/paths/to/*desc-scaled_bold.nii.gz"]

    """
    # Validate parameters
    for chk_dir in [proj_dir, work_dir, log_dir, tplflow_dir]:
        if not os.path.exists(chk_dir):
            raise FileNotFoundError(f"Expected directory : {chk_dir}")
    for chk_file in [fs_license, sing_afni, sing_fmriprep]:
        if not os.path.exists(chk_file):
            raise FileNotFoundError(f"Expected file : {chk_file}")
    if not isinstance(fd_thresh, float):
        raise TypeError("Expected type float for fd_thresh")
    if not isinstance(ignore_fmaps, bool):
        raise TypeError("Expected type bool for ignore_fmaps")
    if not isinstance(no_freesurfer, bool):
        raise TypeError("Expected type bool for no_freesurfer")

    # Setup working and final directories
    proj_raw = os.path.join(proj_dir, "rawdata")
    proj_deriv = os.path.join(proj_dir, "derivatives/pre_processing")
    proj_fp = os.path.join(proj_deriv, "fmriprep")
    proj_fsl = os.path.join(proj_deriv, "fsl_denoise")
    work_deriv = os.path.join(work_dir, "pre_processing")
    work_fp = os.path.join(work_deriv, "fmriprep")
    work_fsl = os.path.join(work_deriv, "fsl_denoise")
    for _dir in [proj_fp, proj_fsl, work_deriv, work_fp, work_fsl]:
        if not os.path.exists(_dir):
            os.makedirs(_dir)

    #
    fp_dict = pp.fmriprep(
        subj,
        proj_raw,
        work_deriv,
        sing_fmriprep,
        tplflow_dir,
        fs_license,
        fd_thresh,
        ignore_fmaps,
        no_freesurfer,
        log_dir,
        False,
    )

    fp_dict["scaled"] = pp.fsl_preproc(
        work_fsl,
        fp_dict,
        sing_afni,
        subj,
        log_dir,
        False,
    )
    return fp_dict


# %%
# def model(
#     subj,
#     sess,
#     proj_dir,
#     work_dir,
#     log_dir,
#     user_name,
#     model_name,
# ):
#     """Conduct FSL modelling.

#     TODO

#     Steps:
#         -   Generate confounds files
#         -   Write setup files
#         -   First-level modeling
#         -   Second-level modeling

#     Returns
#     -------
#     dict
#         Paths to files relevant for workflows.target_id

#     """
#     # Validate user args
#     for chk_dir in [proj_dir, work_dir, log_dir]:
#         if not os.path.exists(chk_dir):
#             raise FileNotFoundError(f"Expected directory : {chk_dir}")
#     if model_name not in ["rest"]:
#         raise ValueError(f"Unexpected model name : {model_name}")

#     # Setup
#     task = "task-rest"
#     proj_deriv = os.path.join(proj_dir, "derivatives")
#     subj_work = os.path.join(
#         work_dir, f"model_fsl-{model_name}", subj, sess, "func"
#     )
#     subj_final = os.path.join(proj_deriv, "model_fsl", subj, sess)
#     for _dir in [subj_work, subj_final]:
#         if not os.path.exists(_dir):
#             os.makedirs(_dir)

#     # Make confounds from fMRIPrep confounds
#     fp_path = os.path.join(
#         work_dir, "pre_processing/fmriprep", subj, sess, "func"
#     )
#     fp_conf_list = sorted(glob.glob(f"{fp_path}/*{task}*timeseries.tsv"))
#     if not fp_conf_list:
#         raise FileNotFoundError(
#             f"Expected fMRIPrep confounds files in {fp_path}"
#         )
#     for conf_path in fp_conf_list:
#         _ = resources.model.confounds(conf_path, subj_work, num_dummy=4)

#     # Make, execute first-level design files
#     design_list = resources.model.write_first_fsf(
#         subj, sess, task, model_name, work_dir, proj_deriv
#     )
#     for fsf_path in design_list:
#         _ = resources.model.run_feat(
#             fsf_path, subj, sess, model_name, "first", log_dir, user_name
#         )


# %%
def omnibus(
    subj,
    sess,
    proj_dir,
    work_dir,
    log_dir,
    user_name,
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
    user_name : str
        DCC login user name
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
    model_keys = ["model_name"]
    for chk_key in model_keys:
        if chk_key not in model_args.keys():
            raise KeyError(f"Expected key {chk_key} in model_args")

    # Trigger workflows
    fp_dict = run_preprocess(
        subj,
        sess,
        proj_dir,
        work_dir,
        log_dir,
        user_name,
        preproc_args["sing_fmriprep"],
        preproc_args["tplflow_dir"],
        preproc_args["fs_license"],
        preproc_args["fd_thresh"],
        preproc_args["ignore_fmaps"],
        preproc_args["no_freesurfer"],
        preproc_args["sing_afni"],
    )
    print(f"\n\nPreproc Finished, fp_dict :\n\n{fp_dict}\n")
    # model(
    #     subj,
    #     sess,
    #     proj_dir,
    #     work_dir,
    #     log_dir,
    #     user_name,
    #     model_args["model_name"],
    # )

    # TODO write/trigger copy+clean
