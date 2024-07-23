# func_archival

This package conducts preprocessing and first-level modeling of archival rsfMRI data hosted by the [Nathan Kline Institute](http://fcon_1000.projects.nitrc.org/indi/enhanced/index.html). Functionally, this package is a wrapper of [func_preprocess](https://github.com/labarlab-emorep/func_preprocess) and [func_model](https://github.com/labarlab-emorep/func_model), which ensures that all data for the EmoRep project move through the same pipeline.

Contents:
* [Setup](#setup)
* [Requirements](#requirements)
* [Usage](#usage)
* [Functionality](#functionality)


## Setup
* Install into project environment on the Duke Compute Cluster (DCC: see [here](https://github.com/labarlab/conda_dcc#conda_dcc))
* Follow setup instructions for [func_preprocess](https://github.com/labarlab-emorep/func_preprocess?tab=readme-ov-file#setup)
* Follow setup instructions for [func_model](https://github.com/labarlab-emorep/func_model#setup), specifically the `fsl_model` section


## Requirements
In addition to any requrements specified for [func_preprocess](https://github.com/labarlab-emorep/func_preprocess) and [func_model](https://github.com/labarlab-emorep/func_model), this package requires:
* `func_process` version >= 2.3.0
* `func_model` version >=4.0.0


## Usage
The CLI supplies a number of parameters (as well as their corresponding default arguments when optional) that allow the user to specify the subject and session of the data to be processed. Trigger help and usage via `$func_archival`:

```
(emorep)[nmm51-dcc: ~]$func_archival
usage: func_archival [-h] [--ignore-fmaps] [--fd-thresh FD_THRESH] [--sessions {ses-BAS1} [{ses-BAS1} ...]]
                     [--preproc-type {scaled,smoothed}] [--proj-dir PROJ_DIR] -s SUBJ_LIST [SUBJ_LIST ...]

Version : 1.2.0

Run processing workflows for single subject.

Move archival data through preprocessing and FSL modeling. Wraps
methods used for Exp2_Compute_Emotion.

Example
-------
func_archival -s sub-08326
func_archival \
    -s sub-08326 \
    --preproc-type smoothed

optional arguments:
  -h, --help            show this help message and exit
  --ignore-fmaps        Whether fmriprep will ignore fmaps,
                        True if "--ignore-fmaps" else False.
  --fd-thresh FD_THRESH
                        Framewise displacement threshold
                        (default : 0.5)
  --sessions {ses-BAS1} [{ses-BAS1} ...]
                        List of BIDS session identifiers
                        (default : ['ses-BAS1'])
  --preproc-type {scaled,smoothed}
                        Determine whether to use scaled or smoothed preprocessed EPIs
                        (default : scaled)
  --proj-dir PROJ_DIR   Path to BIDS-formatted project directory
                        (default : /hpc/group/labarlab/EmoRep/Exp3_Classify_Archival/data_mri_BIDS)

Required Arguments:
  -s SUBJ_LIST [SUBJ_LIST ...], --subj-list SUBJ_LIST [SUBJ_LIST ...]
                        List of subject IDs to submit for processing

```
Workflows for the EmoRep project used default options (e.g. with scaled data and an FD threshold of 0.5).


## Functionality
For each subject and session specified, this workflow will:
1. Conduct preprocessing via [func_preprocess](https://github.com/labarlab-emorep/func_preprocess):
    1. Download rawdata from Keoki
    1. Pre-run FreeSurfer
    1. Run fMRIPrep
    1. Conduct extra preprocessing
    1. Upload output to Keoki
1. Conduct FSL first-level models for resting state via [func_model](https://github.com/labarlab-emorep/func_model):
    1. Download data from Keoki
    1. Generate confound files
    1. Build a design FSF file from pre-generated templates
    1. Execute design via FSL `feat`
    1. Upload output to Keoki

Preprocessed output is organized in the derivatives sub-directory 'pre_processing':

```
derivatives/pre_processing/
├── fmriprep
│   ├── sub-08326
│   ├── sub-08326_ses-BAS1.html
│   ..
│   ├── sub-89407
│   └── sub-89407_ses-BAS1.html
├── freesurfer
│   └── ses-BAS1
│      ├── sub-08326
│      ..
│      └── sub-89407
└── fsl_denoise
    ├── sub-08326
    ..
    └── sub-89407
```
Where fmriprep and fsl_denoise are BIDS-organized, but freesurfer inverts the session and subject organization. The fmriprep and freesurfer directories are organized according to the defaults of those software suites, and fsl_denoise employs the BIDS organization with an added `desc-scaled|smoothed` field.

Modeled output is organized in the derivatives sub-directory 'model_fsl':

```
derivatives/model_fsl/
├── sub-08326
│   └── ses-BAS1
│       └── func
│           ├── confounds_files
│           │   └── sub-08326_ses-BAS1_task-rest_acq-1400_run-01_desc-confounds_timeseries.txt
│           ├── confounds_proportions
│           │   └── sub-08326_ses-BAS1_task-rest_acq-1400_run-01_desc-confounds_proportion.json
│           ├── design_files
│           │   └── run-01_level-first_name-rest_design.fsf
│           └── run-01_level-first_name-rest.feat
│               └── various_fsl_directories
..
└── sub-89407
    └── ses-BAS1
        └── func
            ├── confounds_files
            │   └── sub-89407_ses-BAS1_task-rest_acq-1400_run-01_desc-confounds_timeseries.txt
            ├── confounds_proportions
            │   └── sub-89407_ses-BAS1_task-rest_acq-1400_run-01_desc-confounds_proportion.json
            ├── design_files
            │   └── run-01_level-first_name-rest_design.fsf
            └── run-01_level-first_name-rest.feat
                └── various_fsl_directories

```
Where confounds_files and design_files directories contain their respective confounds or design files, confounds_proportions has a JSON detailing the number and proportion or volumes that were censored, and the `feat` directory is named according to the run, level, and model name.