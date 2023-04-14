"""Methods for submitting BASH commands to subprocess or SLURM scheduler.

ScheduleWorkflow : Generate and submit workflows to the scheduler for each
                    or all pipeline steps.
schedule_subprocess : submit a bash job to the scheduler.
submit_subprocess : submit a bash job as a subprocess.

"""
import os
import sys
import textwrap
import subprocess


class ScheduleWorkflow:
    """Schedule preprocessing workflow.

    Generate workflow scripts for each or all
    processing steps, then submit worklfow to
    SLURM scheduler.

    Attributes
    ----------
    py_script : str, os.PathLike
        Location of workflow script

    Methods
    -------
    omnibus(*args)
        Generate omnibus workflow script
    submit()
        Submit workflow script as SBATCH job

    Example
    -------
    sw = ScheduleWorkflow(*args)
    sw.omnibus(*args)
    sw.submit()

    """

    def __init__(
        self,
        subj,
        sess,
        proj_dir,
        work_dir,
        log_dir,
        user_name,
    ):
        """Initialize.

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

        """
        self._subj = subj
        self._sess = sess
        self._proj_dir = proj_dir
        self._work_dir = work_dir
        self._log_dir = log_dir
        self._user_name = user_name

    def _sbatch_head(self) -> str:
        """Return sbatch preamble."""
        return f"""\
            #!/bin/env {sys.executable}
            #SBATCH --job-name=p{self._subj[4:]}
            #SBATCH --output={self._log_dir}/par{self._subj[4:]}.txt
            #SBATCH --time=30:00:00
            #SBATCH --mem=4000
        """

    # def preprocess(
    #     self,
    #     sing_fmriprep,
    #     tplflow_dir,
    #     fs_license,
    #     fd_thresh,
    #     ignore_fmaps,
    #     no_freesurfer,
    #     sing_afni,
    # ):
    #     """Write preprocess workflow script.

    #     Make a workflow call for a single session of a subject.
    #     Saves script to:
    #         <log_dir>/run_preprocess_<subj>_<sess>.py

    #     Parameters
    #     ----------
    #     sing_fmriprep : str, os.PathLike
    #         Location and image of fmriprep singularity file
    #     tplflow_dir : str, os.PathLike
    #         Clone location of templateflow
    #     fs_license : str, os.PathLike
    #         Location of FreeSurfer license
    #     fd_thresh : float
    #         Threshold for framewise displacement
    #     ignore_fmaps : bool
    #         Whether to incorporate fmaps in preprocessing
    #     no_freesurfer : bool
    #         Whether to use the --fs-no-reconall option
    #     sing_afni : str, os.PathLike
    #         Location of afni singularity image

    #     """
    #     py_cmd = f"""{self._sbatch_head()}
    #         from func_process import workflows
    #         workflows.preprocess(
    #             "{self._subj}",
    #             "{self._sess}",
    #             "{self._proj_dir}",
    #             "{self._work_dir}",
    #             "{self._log_dir}",
    #             "{self._user_name}",
    #             "{sing_fmriprep}",
    #             "{tplflow_dir}",
    #             "{fs_license}",
    #             {fd_thresh},
    #             {ignore_fmaps},
    #             {no_freesurfer},
    #             "{sing_afni}"
    #         )
    #     """
    #     sbatch_cmd = textwrap.dedent(py_cmd)
    #     self._write_script("preprocess", sbatch_cmd)

    # def model(self, model_name):
    #     """Write model workflow script.

    #     Desc.

    #     Parameters
    #     ----------
    #     TODO

    #     """
    #     py_cmd = f"""{self._sbatch_head()}
    #         from func_process import workflows
    #         workflows.model(
    #             "{self._subj}",
    #             "{self._sess}",
    #             "{self._proj_dir}",
    #             "{self._work_dir}",
    #             "{self._log_dir}",
    #             "{self._user_name}",
    #             "{model_name}",
    #         )
    #     """
    #     sbatch_cmd = textwrap.dedent(py_cmd)
    #     self._write_script("model", sbatch_cmd)

    def _write_script(self, wf_name: str, wf_cmd: str):
        """Write generated workflow command to script."""
        self.py_script = os.path.join(
            self._log_dir, f"run_{wf_name}_{self._subj}_{self._sess}.py"
        )
        with open(self.py_script, "w") as ps:
            ps.write(wf_cmd)

    def omnibus(self, preproc_args, model_args):
        """Write preprocess workflow script.

        Make a workflow call for a single session of a subject.
        Saves script to:
            <log_dir>/run_omnibus_<subj>_<sess>.py

        Parameters
        ----------
        preproc_args : dict
            Argument and parameter specific for workflows.preprocess,
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
            -  ["model_name"] = name of FSL model

        """
        py_cmd = f"""{self._sbatch_head()}
            from func_process import workflows
            workflows.omnibus(
                "{self._subj}",
                "{self._sess}",
                "{self._proj_dir}",
                "{self._work_dir}",
                "{self._log_dir}",
                "{self._user_name}",
                {preproc_args},
                {model_args},
            )
        """
        sbatch_cmd = textwrap.dedent(py_cmd)
        self._write_script("omnibus", sbatch_cmd)

    def submit(self):
        """Submit python script to SLURM scheduler."""
        if not hasattr(self, "py_script"):
            raise AttributeError(
                "Please generate workflow script before envoking submit."
            )
        sp_job = subprocess.Popen(
            f"sbatch {self.py_script}",
            shell=True,
            stdout=subprocess.PIPE,
        )
        sp_out, _ = sp_job.communicate()
        print(f"{sp_out.decode('utf-8')}\tfor {self._subj}, {self._sess}")


def schedule_subprocess(
    bash_cmd,
    job_name,
    log_dir,
    user_name,
    num_hours=1,
    num_cpus=1,
    mem_gig=4,
):
    """Run bash commands as scheduled subprocesses.

    Parameters
    ----------
    bash_cmd : str
        Bash syntax, work to schedule
    job_name : str
        Name for scheduler
    log_dir : Path
        Location of output dir for writing logs
    user_name : str
        DCC login user name
    num_hours : int, optional
        Walltime to schedule
    num_cpus : int, optional
        Number of CPUs required by job
    mem_gig : int, optional
        Job RAM requirement for each CPU (GB)

    Returns
    -------
    tuple
        [0] = stdout of subprocess
        [1] = stderr of subprocess

    Notes
    -----
    Avoid using double quotes in <bash_cmd> (particularly relevant
    with AFNI) to avoid conflict with --wrap syntax.

    """
    sbatch_cmd = f"""
        sbatch \
        -J {job_name} \
        -t {num_hours}:00:00 \
        --cpus-per-task={num_cpus} \
        --mem-per-cpu={mem_gig}000 \
        -o {log_dir}/out_{job_name}.log \
        -e {log_dir}/err_{job_name}.log \
        --wait \
        --wrap="{bash_cmd}"
    """
    print(f"Submitting SBATCH job:\n\t{sbatch_cmd}\n")
    job_out, job_err = submit_subprocess(sbatch_cmd)
    return (job_out, job_err)


def submit_subprocess(job_cmd: str) -> tuple:
    """Submit bash as subprocess and return stdout, stderr."""
    job_sp = subprocess.Popen(job_cmd, shell=True, stdout=subprocess.PIPE)
    job_out, job_err = job_sp.communicate()
    job_sp.wait()
    return (job_out, job_err)
