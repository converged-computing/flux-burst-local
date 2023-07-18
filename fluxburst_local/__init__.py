# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

from fluxburst_local.version import __version__

assert __version__


def init(dataclass, **kwargs):
    """
    Parse custom arguments and return the Burst client.

    We use this section to create (and enter) the initial
    FluxBurst local setup. If this is running on top of Flux,
    this means starting another flux instance with the resources.
    If SLURM we assume we are inside a SLURM allocation.
    """
    from .plugin import BurstParameters, FluxBurstHPC

    if not isinstance(dataclass, BurstParameters):
        raise ValueError("Current support is only for BurstParameters")
    FluxBurstHPC.setup(dataclass)
    return FluxBurstHPC(dataclass, **kwargs)
