#!/usr/bin/env python3

import argparse
import os

# Burst slurm allocation
# This is an example of bursting on a slurm allocation from one set of nodes (online)
# to a set that aren't started yet.
from fluxburst.client import FluxBurst

# How we provide custom parameters to a flux-burst plugin
from fluxburst_local.plugin import SlurmBurstParameters

# Save data here
here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Experimental Bursting",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--network-device", help="Network device to use for brokers", default="eth0"
    )
    parser.add_argument("--config-dir", help="Configuration directory for flux")
    parser.add_argument(
        "--curve-cert", help="Curve certificate for flux (flux keygen curve.cert)"
    )
    parser.add_argument(
        "--flux-root", help="Flux root (should correspond with broker running Flux)"
    )
    return parser


def main():
    """
    Create an external cluster we can burst to, and optionally resize.
    """
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    # Create the dataclass for the plugin config
    # We use a dataclass because it does implicit validation of required params, etc.
    params = SlurmBurstParameters(
        flux_root=args.flux_root,
        config_dir=args.config_dir,
        curve_cert=args.curve_cert,
        network_device=args.network_device,
    )
    client = FluxBurst()

    # For debugging, here is a way to see plugins available
    # import fluxburst.plugins as plugins
    # print(plugins.burstable_plugins)
    # {'gke': <module 'fluxburst_gke' from '/home/flux/.local/lib/python3.8/site-packages/fluxburst_gke/__init__.py'>}

    # Load our plugin and provide the dataclass to it!
    client.load("local", params)

    # Sanity check loaded
    print(f"flux-burst client is loaded with plugins for: {client.choices}")

    # We are using the default algorithms to filter the job queue and select jobs.
    # If we weren't, we would add them via:
    # client.set_ordering()
    # client.set_selector()

    # Here is how we can see the jobs that are contenders to burst!
    # client.select_jobs()

    # Now let's run the burst! The active plugins will determine if they
    # are able to schedule a job, and if so, will do the work needed to
    # burst. unmatched jobs (those we weren't able to schedule) are
    # returned, maybe to do something with? Note that the default mock
    # generates a N=4 job. For compute engine that will be 3 compute
    # nodes and 1 login node.
    unmatched = client.run_burst()
    assert not unmatched
    plugin = client.plugins["compute_engine"]
    print(
        f"Terraform configs and working directory are found at {plugin.params.terraform_dir}"
    )
    input("Press Enter to when you are ready to destroy...")

    # Get a handle to the plugin so we can cleanup!
    plugin.cleanup()


if __name__ == "__main__":
    main()
