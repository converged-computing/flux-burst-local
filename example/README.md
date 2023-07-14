# Flux Burst Local Examples

This will include examples for local bursting.

## SLURM

For this first use case, we assume that we have some allocation we are sitting on
with N resources, and we want to start a lead broker at index 0 and then allow bursting
to 1-N. This example varies slightly in comparison to the others because
it will both create the lead broker _and_ then run flux-burst using the plugin
to do the birst, while the others assume starting already instead the running
lead broker. We are choosing this design because likely a local burst will need
to do (and automate) both steps.

```bash
# If you are using a custom flux install
$ python burst-slurm-allocation.py --config-dir ./configs --flux-root /path/to/flux/root --network-device eno1

# If you want to discover flux on your path
$ python burst-slurm-allocation.py --config-dir ./configs --network-device eno1

# Development with one node (e.g., DevContainer)
$ python3 burst-slurm-allocation.py --config-dir ./configs --network-device eno1 --hostnames $(hostname)
```

Note that the flux root should have lib, bin, libexec, etc. in it. It's the `--prefix`
you chose for the install.
