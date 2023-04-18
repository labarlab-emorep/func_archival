"""Methods for submitting BASH commands to subprocess or SLURM scheduler."""
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
    run_all(**args)
        Generate omnibus workflow script
    submit()
        Submit workflow script as SBATCH job

    Example
    -------
    sw = ScheduleWorkflow(**args)
    sw.run_all(**args)
    sw.submit()

    """

    def __init__(
        self,
        subj,
        sess,
        proj_dir,
        work_dir,
        log_dir,
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

        """
        self._subj = subj
        self._sess = sess
        self._proj_dir = proj_dir
        self._work_dir = work_dir
        self._log_dir = log_dir

    def _sbatch_head(self) -> str:
        """Return sbatch preamble."""
        return f"""\
            #!/bin/env {sys.executable}
            #SBATCH --job-name=p{self._subj[4:]}
            #SBATCH --output={self._log_dir}/par{self._subj[4:]}.txt
            #SBATCH --time=30:00:00
            #SBATCH --mem=4000
        """

    def _write_script(self, wf_name: str, wf_cmd: str):
        """Write generated workflow command to script."""
        self.py_script = os.path.join(
            self._log_dir, f"run_{wf_name}_{self._subj}_{self._sess}.py"
        )
        with open(self.py_script, "w") as ps:
            ps.write(wf_cmd)

    def run_all(self, preproc_args, model_args):
        """Write preprocess workflow script.

        Make a workflow call for a single session of a subject.
        Saves script to:
            <log_dir>/run_omnibus_<subj>_<sess>.py

        Parameters
        ----------
        preproc_args : dict
            Argument and parameter specific for preprocessing
            portion of preproc_model
        model_args : dict
            Same as preproc_args, but for modeling portion of
            preproc_model

        """
        py_cmd = f"""{self._sbatch_head()}
            from func_archival import workflows
            workflows.preproc_model(
                "{self._subj}",
                "{self._sess}",
                "{self._proj_dir}",
                "{self._work_dir}",
                "{self._log_dir}",
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
