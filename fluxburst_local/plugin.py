# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


import os
import shutil
from dataclasses import dataclass
from typing import Optional

import fluxburst.utils as utils
from fluxburst.logger import logger
from fluxburst.plugins import BurstPlugin

import fluxburst_local.templates as templates


@dataclass
class BurstParameters:
    """
    Custom parameters for SLURM.

    It should be possible to read this in from yaml, or the
    environment (or both).
    """

    hostnames: str
    port: int = 8050
    network_device: str = "eth0"

    # Custom broker config / curve certs for bursted cluster
    curve_cert: Optional[str] = None
    flux_root: Optional[str] = None
    config_dir: Optional[str] = None

    # Flux log level
    log_level: Optional[int] = 7

    # Custom flux user (defaults to running user)
    flux_user: Optional[str] = None

    def ensure_path(self):
        """
        Ensure flux bin is on the path
        """
        # Ensure flux root on path
        path = os.environ.get("PATH")
        if f":{self.flux_root}/bin:" not in path:
            path = f"{self.flux_root}/bin:{path}"
        os.environ.putenv("PATH", path)
        os.environ["PATH"] = path

    @property
    def fluxcmd(self):
        return f"{self.flux_root}/bin/flux"

    def generate_flux_config(self):
        """
        Generate a bursted broked config.
        """
        template = templates.system_toml

        # We call this a poor man's jinja2!
        replace = {
            "NODELIST": self.hostnames,
            "PORT": self.port,
            "CURVECERT": self.curve_cert,
            "NETWORK_DEVICE": self.network_device,
            "CONFIG_DIR": self.config_dir,
            "FLUXROOT": self.flux_root,
        }
        for key, value in replace.items():
            template = template.replace(key, value)

        # Write the system toml
        system_toml = os.path.join(self.config_dir, "system.toml")
        print(f"Writing flux config to {system_toml}")
        utils.write_file(template, system_toml)
        dataclass.system_toml = template

    def validate(self):
        """
        Validate flux path exists.
        """
        # If we aren't given a flux root, try to find one
        if not self.flux_root:
            flux = shutil.which("flux")
            if flux:
                self.flux_root = os.path.dirname(os.path.dirname(flux))
        if not os.path.exists(self.flux_root):
            raise ValueError(
                "flux must be on the path, OR flux_root must be defined and exist."
            )
        print(f"🌳️ Flux root set to {self.flux_root}")

    def set_config_dir(self):
        """
        Setup the local config directory
        """
        self.config_dir = os.path.abspath(self.config_dir or utils.get_tmpdir())
        utils.mkdir_p(self.config_dir)

    def write_curve_cert(self):
        """
        Ensure we have a curve cert string and write to file.
        """
        # If we are given a filepath, copy it over
        curve_path = os.path.join(self.config_dir, "curve.cert")
        if (
            self.curve_cert
            and os.path.exists(self.curve_cert)
            and not os.path.exists(curve_path)
        ):
            shutil.copyfile(self.curve_cert, curve_path)
            self.curve_cert = curve_path
            return

        res = utils.run_command([self.fluxcmd, "keygen", curve_path])
        if res["return_code"] != 0:
            raise ValueError(
                f'Issue generating curve-cert: {res["message"]}. Try pre-generating it with flux keygen {curve_path}.'
            )
        utils.write_file(res["message"], curve_path)
        self.curve_cert = curve_path

    def write_resource_spec(self):
        """
        Use flux R encode to write resource spec for hosts.
        """
        rpath = os.path.join(self.config_dir, "R")

        # Otherwise not defined, we can't proceed!
        res = utils.run_command(
            [self.fluxcmd, "R", "encode", "--hosts", self.hostnames, "--local"]
        )
        if res["return_code"] != 0:
            raise ValueError("Issue generating R")
        utils.write_file(res["message"], rpath)


@dataclass
class SlurmBurstParameters(BurstParameters):
    """
    Custom parameters for SLURM.

    We can get the hostnames from the environment. This dataclass
    is used to trigger getting the needed parameters from the environment.
    """

    hostnames: Optional[str] = None

    def set_hostnames(self):
        """
        Ensure we have hostnames from a variable or environment.
        """
        self.hostnames = self.hostnames or os.environ.get("SLURM_JOB_HOSTLIST")
        self.hostnames = "quartz[1-2]"
        if not self.hostnames:
            raise ValueError(
                "The 'hostnames' parameter or environment variable SLURM_JOB_HOSTLIST must be defined."
            )


class FluxBurstSlurm(BurstPlugin):
    # Set our custom dataclass, otherwise empty
    _param_dataclass = SlurmBurstParameters

    @classmethod
    def setup(cls, dataclass):
        """
        Finish populating the dataclass with SLURM environment variables.
        """
        dataclass.validate()
        dataclass.set_hostnames()
        dataclass.set_config_dir()
        dataclass.write_curve_cert()
        dataclass.write_resource_spec()
        dataclass.generate_flux_config()
        # TODO we need to start our main broker here and connect to it

    def run(self, request_burst=False, nodes=None, tasks=None):
        """
        Given some set of scheduled jobs, run bursting.
        """
        print("TODO WRITE ME VANESSA")
        print("BURST")
        import IPython

        IPython.embed()

        # Exit early if no jobs to burst
        if not self.jobs and not request_burst:
            logger.info(f"Plugin {self.name} has no jobs to burst.")
            return

        # If we have requested a burst, nodes are required
        if request_burst and not nodes:
            logger.warning("Burst requests require a number of nodes.")
            return

        # Request a burst with some number of nodes and tasks, vs. derive from jobs
        if request_burst:
            node_count = nodes
        else:
            # For now, assuming one burst will be done to run all jobs,
            # we just get the max size. This is obviously not ideal
            node_count = max([v["nnodes"] for _, v in self.jobs.items()])
        assert node_count

    def validate_params(self):
        """
        Validate parameters provided as BurstParameters.

        This includes checking to see if we have an isolated burst,
        and if a script is provided for any boot script, ensuring that
        it exists.
        """
        if not os.path.exists(self.params.flux_root):
            logger.error(f"Flux root {self.params.flux_root} does not exist.")
            return False
        return True

    def schedule(self, job):
        """
        Given a burstable job, determine if we can schedule it.

        This function should also consider logic for deciding if/when to
        assign clusters, but run should actually create/destroy.
        """
        # If it's not an isolated burst and we don't have host variables, no go
        if not self.validate_params():
            return False

        # TODO determine if we can match some resource spec to another,
        # We likely want this class to be able to generate a lookup of
        # instances / spec about them.

        # For now, we just accept anything, and add to our jobs and return true
        if job["id"] in self.jobs:
            logger.debug(f"{job['id']} is already scheduled")
            return True

        # Add to self.jobs and return True!
        self.jobs[job["id"]] = job
        return True
