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

    hostnames: Optional[str] = None
    port: Optional[int] = 8050
    network_device: Optional[str] = "eth0"

    # Custom broker config / curve certs for bursted cluster
    curve_cert: Optional[str] = None
    flux_root: Optional[str] = None
    config_dir: Optional[str] = None
    flux_uri: Optional[str] = None

    # Flux log level
    log_level: Optional[int] = 7
    regenerate: bool = False

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
        system_toml = os.path.join(self.system_dir, "system.toml")
        if os.path.exists(system_toml) and not self.regenerate:
            return

        # We call this a poor man's jinja2!
        replace = {
            "NODELIST": self.hostnames,
            "PORT": str(self.port),
            "CURVECERT": self.curve_cert,
            "NETWORK_DEVICE": self.network_device,
            "CONFIG_DIR": self.config_dir,
            "FLUXROOT": self.flux_root,
        }
        for key, value in replace.items():
            template = template.replace(key, value)

        # Write the system toml
        print(f"🦩️ Writing flux config to {system_toml}")
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

        We also create paths for run, lib, and system.
        """
        self.config_dir = os.path.abspath(self.config_dir or utils.get_tmpdir())
        self.system_dir = os.path.join(self.config_dir, "system")
        self.run_dir = os.path.join(self.config_dir, "run")
        self.lib_dir = os.path.join(self.config_dir, "run")
        for path in [self.lib_dir, self.run_dir, self.system_dir]:
            utils.mkdir_p(path)

    def write_curve_cert(self):
        """
        Ensure we have a curve cert string and write to file.
        """
        # If we are given a filepath, copy it over
        curve_path = os.path.join(self.config_dir, "curve.cert")

        # Cut out early if we are good!
        if os.path.exists(curve_path):
            return

        if (
            self.curve_cert is not None
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
        self.curve_cert = curve_path

    def write_resource_spec(self):
        """
        Use flux R encode to write resource spec for hosts.
        """
        rpath = os.path.join(self.config_dir, "R")
        if os.path.exists(rpath) and not self.regenerate:
            return

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

    def set_hostnames(self):
        """
        Ensure we have hostnames from a variable or environment.
        """
        self.hostnames = (
            self.hostnames
            or os.environ.get("SLURM_JOB_HOSTLIST")
            or os.environ.get("SLURM_NODELIST")
        )
        if not self.hostnames:
            raise ValueError(
                "The 'hostnames' parameter or environment variable SLURM_JOB_HOSTLIST must be defined."
            )


class FluxBurstLocal(BurstPlugin):
    _param_dataclass = BurstParameters

    def run(self, request_burst=False, nodes=None, **kwargs):
        """
        Given some set of scheduled jobs, run bursting.
        """
        try:
            import flux
            import flux.resource
        except ImportError:
            logger.info("Cannot connect to flux broker, cannot burst.")
            return

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

        handle = flux.Flux()
        rpc = flux.resource.list.resource_list(handle)
        listing = rpc.get()

        nodes_down = [node for node in listing.down.nodelist]
        nodes_free = [node for node in listing.free.nodelist]
        if nodes_free + nodes_down < node_count:
            logger.warning("Not enough nodes to satisfy job, even with bursting")
            return

        # Calculate nodes needed and burst. Ensure if we don't need any, we exit
        nodes_needed = node_count - nodes_free
        if nodes_needed <= 0:
            return

        logger.debug(f"{nodes_needed} are needed.")

        # Note that this assumes flux in the same install location, and the rank 0 of the second instance == rank 0 of the first
        # Aside from that, we let flux choose the nodes
        command = [
            self.params.fluxcmd,
            "proxy",
            self.params.flux_uri,
            self.params.fluxcmd,
            "-N",
            nodes_needed,
            "--requires" '"not rank:0"',
            self.params.fluxcmd,
            "start",
            "--broker-opts",
            "--config",
            self.params.system_dir,
        ]
        print(command)
        res = utils.run_command(command)
        if res["return_code"] != 0:
            logger.error(f"Issue connecting to flux proxy: {res['message']}.")

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
        if not self.params.flux_uri:
            logger.error("A Flux URI (flux_uri parameter) is required to burst.")
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


class FluxBurstSlurm(FluxBurstLocal):
    # Set our custom dataclass, otherwise empty
    _param_dataclass = BurstParameters

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

        # Flux URI is required
        if not dataclass.flux_uri:
            raise ValueError(
                "The flux_uri must be defined to provide to the child instance."
            )

        # Generate the rundirectory
        # Start the main broker via replacing current process
        flux_burst_local = shutil.which("flux-burst-local")
        if not flux_burst_local:
            raise ValueError("Cannot find flux-burst-local executable on path.")
        args = [
            "start",
            "--broker-opts",
            "--config",
            dataclass.system_dir,
            "-Stbon.fanout=256",
            f"-Srundir={dataclass.run_dir}",
            f"-Sstatedir={dataclass.lib_dir}",
            f"-Slocal-uri=local://{dataclass.run_dir}/local",
            f"-Slog-stderr-level={dataclass.log_level}",
            "-Slog-stderr-mode=local",
            "-Sbroker.quorum=0",
            flux_burst_local,
            "--config-dir",
            dataclass.system_dir,
            "--flux-root",
            dataclass.flux_root,
            "--flux-uri",
            dataclass.flux_uri,
        ]
        print(
            "🌀️ Done! Use the following command to start your Flux instance and burst!"
        )

        # Write the command file
        command_file = os.path.join(dataclass.config_dir, "start.sh")
        print(f"    It is also written to {command_file}\n")
        command = f"{dataclass.fluxcmd} {' '.join(args)}"
        command_exec = f"#!/bin/bash\n{command}"
        utils.write_file(command_exec, command_file)
        print(f"{dataclass.fluxcmd} {' '.join(args)}")
