#!/usr/bin/env python

# This is a script called by flux-burst-local, and it's assumed that files
# are generated in the directed config directory, and we've started the
# main broker and can now burst.

import argparse
import time

from fluxburst.client import FluxBurst

# How we provide custom parameters to a flux-burst plugin
from fluxburst_local.plugin import BurstParameters


def get_parser():
    parser = argparse.ArgumentParser(
        description="Flux Local Broker Start",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--config-dir", help="Configuration directory for flux")
    parser.add_argument(
        "--flux-root", help="Flux root (should correspond with broker running Flux)"
    )
    parser.add_argument(
        "--flux-uri", help="URI for the parent instance (to bring nodes up)"
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Create the dataclass for the plugin config
    # We use a dataclass because it does implicit validation of required params, etc.
    params = BurstParameters(
        flux_root=args.flux_root,
        config_dir=args.config_dir,
        # This says to not re-generate our configs!
        regenerate=False,
        flux_uri=args.flux_uri,
    )
    assert params
    client = FluxBurst()

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

    # This isn't supported (or needed) for top level flux-burst yet, so
    # we interact directly with the plugin
    plugin = client.plugins["local"]

    # Continue running the burst until no more burstable
    while True:
        print("Running burst...")

        # This will hit the plugin->run to flux proxy to start brokers
        client.run_burst()

        # This is a bit buggy - we have to wait for the brokers to start
        time.sleep(10)

        # Bursted job ids associated with brokers are here
        if plugin.jobids:
            # Ask client to wait for all jobs to be finished (in state cancel or fail)
            client.wait_for_jobs()

            # When they are done, we cleanup the jobs (and clear jobids
            client.run_unburst()

        time.sleep(5)


if __name__ == "__main__":
    main()
