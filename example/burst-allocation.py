#!/usr/bin/env python3

import argparse
import os
import time

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
    parser.add_argument("--flux-uri", help="Flux URI of currently running instance.")
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
        flux_uri=args.flux_uri,
    )
    client = FluxBurst()

    # For debugging, here is a way to see plugins available
    # import fluxburst.plugins as plugins
    # print(plugins.burstable_plugins)

    # Load our plugin and provide the dataclass to it!
    # Unlike other plugins, the local one handles setting up the flux instance
    # (and then issuing the burst). This could change (e.g., if we have already)
    # generated configs or started the cluster.
    client.load("local", params)

    # Continue running the burst until no more burstable
    # This likely needs to be adjusted
    while True:
        print("Running burst...")
        client.run_burst()
        time.sleep(30)


if __name__ == "__main__":
    main()
