# Flux Burst Local Examples

This will include examples for local bursting.

- [Allocation burst](#allocation-burst) walks through early details.
- [Development](#development) is how I developed
- [Testing](#testing) is likely what you want if you want to test this yourself!

## Allocation burst

For this first use case, we assume that we have some allocation we are sitting on
with N resources, and we want to start a lead broker at index 0 and then allow bursting
to 1-N. This example varies slightly in comparison to the others because
it will both create the lead broker _and_ then run flux-burst using the plugin
to do the burst, while the others assume starting already instead the running
lead broker. We are choosing this design because likely a local burst will need
to do (and automate) both steps. The general usage is the following:

### 0. Install Flux Burst

Next we need to install stuff! I did this _outside_ the allocation in case it matters. Likely you will have variance in your Python environment.
I wound up:

1. Using the system Flux + Python
2. Using my local environment pip to install to the python user site
3. Installing flux bindings that matched my version of flux.

I was able to install flux bindings to my local python environment (associated with python 3.6 on the system):

```bash
pip3 install flux-python==0.48.0rc6 --user
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
```

Note there was a bug with dataclasses and I uninstalled it:

```bash
pip3 uninstall dataclasses -y
```

And then the import of Flux worked. Then I make a working directory:

```bash
mkdir test-flux-burst
cd test-flux-burst
```

And installed flux-burst and flux-burst local (you can also clone repositories)

```bash
pip install flux-burst
pip install flux-burst-local
```

You might need to add `--user` if you get a permissions error. Mine installed to my user site by default.

### 1. Create an allocation.

First, create a Flux instance to work from. This is how you do that from SLURM. This would be for four nodes.

```bash
srun -N 4 --time 60:00 -ppdebug --pty flux start
```

When you get the allocation, you can verify your resources as follows:

```bash
$ flux resource list
     STATE NNODES   NCORES NODELIST
      free      4      144 quartz[8-11]
 allocated      0        0
      down      0        0
```

Then generate the configs for the hosts we got. Note that since this is no longer slurm, we won't get them from the environment variable.
I was lazy and grabbed them from `flux resource list` (there likely is a better way!)

```bash
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
export PATH=/g/g0/sochat1/.local/bin:$PATH
cd /usr/workspace/sochat1/test-flux-burst/flux-burst-local/example
python3 burst-allocation.py --config-dir ./configs --network-device "*" --hostnames quartz[5-8] --flux-uri $FLUX_URI
```
```console
$ python3 burst-allocation.py --config-dir ./configs --network-device "*" --hostnames quartz[5-8] --flux-uri $FLUX_URI
🌳️ Flux root set to /usr
🌀️ Done! Use the following command to start your Flux instance and burst!
    It is also written to /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/start.sh

/usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system -Stbon.fanout=256 -Srundir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Sstatedir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Slocal-uri=local:///usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run/local -S pty.interactive -Slog-stderr-level=7 -Slog-stderr-mode=local -Sbroker.quorum=0 /g/g0/sochat1/.local/bin/flux-burst-local --config-dir /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system --flux-root /usr --flux-uri local:///var/tmp/sochat1/flux-TvAVr6/local-0
```

That will generate the entire "configs" directory that you can check before running the command. When you are ready - copy paste the above and run it!

<details>

<summary>Expected output of command</summary>

```console
broker.debug[0]: insmod connector-local
broker.info[0]: start: none->join 14.5897ms
broker.info[0]: parent-none: join->init 0.025185ms
connector-local.debug[0]: allow-guest-user=true
connector-local.debug[0]: allow-root-owner=true
broker.debug[0]: insmod barrier
broker.debug[0]: insmod content-sqlite
content-sqlite.debug[0]: /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run/content.sqlite (22 objects) journal_mode=WAL synchronous=NORMAL
broker.debug[0]: content backing store: enabled content-sqlite
broker.debug[0]: insmod kvs
kvs.info[0]: restored KVS from checkpoint on 2023-07-15T02:17:45Z
broker.debug[0]: insmod kvs-watch
broker.debug[0]: insmod resource
resource.debug[0]: reslog_cb: resource-init event posted
resource.debug[0]: reslog_cb: resource-define event posted
broker.debug[0]: insmod cron
cron.info[0]: synchronizing cron tasks to event heartbeat.pulse
broker.debug[0]: insmod job-manager
job-manager.debug[0]: jobtap plugin .history registered method job-manager.history.get
job-manager.info[0]: restart: 0 jobs
job-manager.info[0]: restart: 0 running jobs
job-manager.debug[0]: restart: max_jobid=0
job-manager.debug[0]: duration-validator: updated expiration to 0.00
broker.debug[0]: insmod job-info
broker.debug[0]: insmod job-list
job-list.debug[0]: job_state_init_from_kvs: read 0 jobs
broker.debug[0]: insmod job-ingest
job-ingest.debug[0]: configuring validator with plugins=(null), args=(null) (enabled)
job-ingest.debug[0]: fluid ts=1ms
broker.debug[0]: insmod job-exec
job-exec.debug[0]: using default shell path /usr/libexec/flux/flux-shell
job-exec.debug[0]: using imp path /usr/libexec/flux/flux-imp
broker.debug[0]: insmod heartbeat
broker.info[0]: rc1.0: running /etc/flux/rc1.d/01-flux-account-priority-update
broker.info[0]: rc1.0: running /etc/flux/rc1.d/01-sched-fluxion
broker.debug[0]: insmod sched-fluxion-resource
sched-fluxion-resource.info[0]: version 0.26.0
sched-fluxion-resource.debug[0]: mod_main: resource module starting
sched-fluxion-resource.warning[0]: create_reader: allowlist unsupported
sched-fluxion-resource.debug[0]: resource graph datastore loaded with rv1exec reader
sched-fluxion-resource.info[0]: populate_resource_db: loaded resources from core's resource.acquire
sched-fluxion-resource.debug[0]: resource status changed (rankset=[all] status=DOWN)
sched-fluxion-resource.debug[0]: mod_main: resource graph database loaded
broker.debug[0]: insmod sched-fluxion-qmanager
sched-fluxion-qmanager.info[0]: version 0.26.0
sched-fluxion-qmanager.debug[0]: service_register
sched-fluxion-qmanager.debug[0]: enforced policy (queue=default): fcfs
sched-fluxion-qmanager.debug[0]: effective queue params (queue=default): default
sched-fluxion-qmanager.debug[0]: effective policy params (queue=default): default
sched-fluxion-qmanager.debug[0]: handshaking with sched-fluxion-resource completed
job-manager.debug[0]: scheduler: hello
job-manager.debug[0]: scheduler: ready unlimited
sched-fluxion-qmanager.debug[0]: handshaking with job-manager completed
broker.info[0]: rc1.0: running /etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: /etc/flux/rc1 Exited (rc=0) 2.1s
broker.info[0]: rc1-success: init->quorum 2.09608s
broker.debug[0]: groups: broker.online=0
broker.info[0]: online: quartz5 (ranks 0)
broker.info[0]: quorum-full: quorum->run 0.101144s
resource.debug[0]: reslog_cb: online event posted
sched-fluxion-resource.debug[0]: resource status changed (rankset=[0] status=UP)
flux-burst client is loaded with plugins for: local
Running burst...
```

</details>

The above is going to sleep every 30 seconds and try to run a burst. Bursting happens based on jobs needing it, so let's do that next!
In another terminal, connect to your same lead broker node and then the local socket (e.g quartz5)

```bash
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
export PATH=/g/g0/sochat1/.local/bin:$PATH
cd /usr/workspace/sochat1/test-flux-burst/flux-burst-local/example
flux proxy local://./configs/run/local
```

You should see all the instances, that the main broker is online and the other nodes offline:

```bash
$ flux resource list
     STATE NNODES   NCORES NODELIST
      free      1       36 quartz5
 allocated      0        0
      down      3      108 quartz[6-8]
```

Now we want to test running a flux job and targeting the three down workers. Submit a burstable job that needs two nodes.

```bash
flux run -N 4 -o cpu-affinity=off --cwd /tmp --setattr=burstable hostname
```

If you are watching the main broker still running, you should see the nodes join. But the problem now is that this command was run from the top level instance,
and not from inside of the burst. There might be a more clever way to run all of this, but the problem (as I see it) is that we are one level too low to control the bursting.
Hmm, can we do a flux proxy to the parent socket?

```bash
flux proxy flux submit -N 3 --requires "not rank:0" /usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system
```


## Development

This is earlier work for development (likely not perfectly relevant anymore, kept for documentation)

```bash
# Ensure the installed executable is on your path
export PATH=$HOME/.local/bin:$PATH

# If you are using a custom flux install
$ python burst-allocation.py --config-dir ./configs --flux-root /path/to/flux/root --network-device eno1

# If you want to discover flux on your path
$ python burst-allocation.py --config-dir ./configs --network-device eno1

# Development with one node (e.g., DevContainer)
$ python3 burst-allocation.py --config-dir ./configs --network-device eno1 --hostnames $(hostname)
```
```
🌳️ Flux root set to /usr
🦩️ Writing flux config to /workspaces/flux-burst-local/example/configs/system/system.toml
🌀️ Done! Use the following command to start your Flux instance and burst!
    It is also written to /workspaces/flux-burst-local/example/configs/start.sh

/usr/bin/flux start --broker-opts --config /workspaces/flux-burst-local/example/configs -Stbon.fanout=256 -Srundir=/workspaces/flux-burst-local/example/configs/run -Sstatedir=/workspaces/flux-burst-local/example/configs/run -Slocal-uri=local:///workspaces/flux-burst-local/example/configs/run/local -Slog-stderr-level=7 -Slog-stderr-mode=local /home/vscode/.local/bin/flux-burst-local --config-dir /workspaces/flux-burst-local/example/configs --flux-root /usr
```

In the above, I was running on SLURM so the hostnames were detected automatically. If you are in
a Flux instance you should use `flux resource list` to get them and provide with `--hostnames`.
Here is what the generated tree looks like under configs:

```bash
tree ./configs
```
```console
$ tree example/configs/
example/configs/
├── curve.cert
├── R
├── run
│   └── content.sqlite
├── start.sh
└── system
    └── system.toml

2 directories, 5 files
```
The sockets (e.g., "local") will be generated under run. And here is what it looks like without the
secondary brokers starting yet:

```console
$ bash configs/start.sh
broker.debug[0]: insmod connector-local
broker.info[0]: start: none->join 0.6186ms
broker.info[0]: parent-none: join->init 0.034561ms
connector-local.debug[0]: allow-guest-user=false
connector-local.debug[0]: allow-root-owner=false
broker.debug[0]: insmod barrier
broker.debug[0]: insmod content-sqlite
content-sqlite.debug[0]: /workspaces/flux-burst-local/example/configs/run/content.sqlite (0 objects) journal_mode=WAL synchronous=NORMAL
broker.debug[0]: content backing store: enabled content-sqlite
broker.debug[0]: insmod kvs
broker.debug[0]: insmod kvs-watch
broker.debug[0]: insmod resource
resource.debug[0]: reslog_cb: resource-init event posted
resource.debug[0]: reslog_cb: resource-define event posted
broker.debug[0]: insmod cron
cron.info[0]: synchronizing cron tasks to event heartbeat.pulse
broker.debug[0]: insmod job-manager
job-manager.debug[0]: jobtap plugin .history registered method job-manager.history.get
job-manager.info[0]: restart: 0 jobs
job-manager.info[0]: restart: 0 running jobs
job-manager.info[0]: restart: checkpoint.job-manager not found
job-manager.debug[0]: restart: max_jobid=ƒ1
job-manager.debug[0]: duration-validator: updated expiration to 0.00
broker.debug[0]: insmod job-info
broker.debug[0]: insmod job-list
job-list.debug[0]: job_state_init_from_kvs: read 0 jobs
broker.debug[0]: insmod job-ingest
job-ingest.debug[0]: configuring validator with plugins=(null), args=(null) (enabled)
job-ingest.debug[0]: fluid ts=1ms
broker.debug[0]: insmod job-exec
job-exec.debug[0]: using default shell path /usr/libexec/flux/flux-shell
broker.debug[0]: insmod heartbeat
broker.info[0]: rc1.0: running /etc/flux/rc1.d/01-sched-fluxion
broker.debug[0]: insmod sched-fluxion-resource
sched-fluxion-resource.info[0]: version 0.27.0-38-ge0b49993
sched-fluxion-resource.debug[0]: mod_main: resource module starting
sched-fluxion-resource.warning[0]: create_reader: allowlist unsupported
sched-fluxion-resource.debug[0]: resource graph datastore loaded with rv1exec reader
sched-fluxion-resource.info[0]: populate_resource_db: loaded resources from core's resource.acquire
sched-fluxion-resource.debug[0]: resource status changed (rankset=[all] status=DOWN)
sched-fluxion-resource.debug[0]: mod_main: resource graph database loaded
broker.debug[0]: insmod sched-fluxion-qmanager
sched-fluxion-qmanager.info[0]: version 0.27.0-38-ge0b49993
sched-fluxion-qmanager.debug[0]: service_register
sched-fluxion-qmanager.debug[0]: enforced policy (queue=default): fcfs
sched-fluxion-qmanager.debug[0]: effective queue params (queue=default): default
sched-fluxion-qmanager.debug[0]: effective policy params (queue=default): default
sched-fluxion-qmanager.debug[0]: handshaking with sched-fluxion-resource completed
job-manager.debug[0]: scheduler: hello
job-manager.debug[0]: scheduler: ready unlimited
sched-fluxion-qmanager.debug[0]: handshaking with job-manager completed
broker.info[0]: rc1.0: running /etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: /etc/flux/rc1 Exited (rc=0) 0.4s
broker.info[0]: rc1-success: init->quorum 0.3982s
broker.debug[0]: groups: broker.online=0
broker.info[0]: online: c35948d1ed31 (ranks 0)
broker.info[0]: quorum-full: quorum->run 0.100979s
resource.debug[0]: reslog_cb: online event posted
sched-fluxion-resource.debug[0]: resource status changed (rankset=[0] status=UP)
TODO START OTHER WOKRERS
...
```

### On Quartz

I was able to install flux bindings to my local python environment (associated with python 3.6 on the system):

```bash
pip3 install flux-python==0.48.0rc6 --user
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
```
Note there was a bug with dataclasses and I uninstalled it:

```bash
pip3 uninstall dataclasses -y
```

And then the import of Flux worked. Then I make a working directory:

```bash
mkdir test-flux-burst
cd test-flux-burst
```

And installed flux-burst and flux-burst local.

```bash
# I needed to do this for package data
pip install flux-burst
git clone -b add/pre-section https://github.com/converged-computing/flux-burst
cd flux-burst
pip3 install . --user
python3 setup.py install --user
cd ../
git clone https://github.com/converged-computing/flux-burst-local
cd flux-burst-local
pip3 install . --user
python3 setup.py install --user
cd ../
```

And added the location where `flux-burst-local` ("binary") is installed to the path:

```bash
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
export PATH=/g/g0/sochat1/.local/bin:$PATH
```

Next let's try starting the main broker, and generating a command for the workers.
Since I'm developing this, I'll need to run this command multiple times as I test
interacting with workers.

```bash
$ cd flux-burst-local/example
$ python3 burst-slurm-allocation.py --config-dir ./configs --network-device "*"
```
```
🌳️ Flux root set to /usr
🌀️ Done! Use the following command to start your Flux instance and burst!
    It is also written to /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/start.sh

/usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system -Stbon.fanout=256 -Srundir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Sstatedir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Slocal-uri=local:///usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run/local -Slog-stderr-level=7 -Slog-stderr-mode=local /g/g0/sochat1/.local/bin/flux-burst-local --config-dir /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs --flux-root /usr
```

Since I didn't know what I was doing, I did the following. First, create a Flux instance to work from:

```bash
srun -N 4 --time 60:00 -ppdebug --pty flux start
```
Then generate the configs for the hosts we got. Note that since this is no longer slurm, we won't get them from the environment variable.
I was lazy and grabbed them from resources:

```bash
$ flux resource list
     STATE NNODES   NCORES NODELIST
      free      4      144 quartz[8-11]
 allocated      0        0
      down      0        0
```

Note that when you ssh in later, you probably won't be connected to this instance. I found the socket in tmp and did:

```bash
flux proxy local:///tmp/sochat1/flux-rL3UfM/local-0
```

And then I was connected again.

```bash
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
export PATH=/g/g0/sochat1/.local/bin:$PATH
cd /usr/workspace/sochat1/test-flux-burst/flux-burst-local/example
python3 burst-slurm-allocation.py --config-dir ./configs --network-device "*" --hostnames quartz[8-11]
```
```console
🌳️ Flux root set to /usr
🦩️ Writing flux config to /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system/system.toml
🌀️ Done! Use the following command to start your Flux instance and burst!
    It is also written to /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/start.sh

/usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system -Stbon.fanout=256 -Srundir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Sstatedir=/usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run -Slocal-uri=local:///usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/run/local -Slog-stderr-level=7 -Slog-stderr-mode=local /g/g0/sochat1/.local/bin/flux-burst-local --config-dir /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system --flux-root /usr
```

Grab the FLUX_URI for this parent instance:

```
$ echo $FLUX_URI
local:///var/tmp/sochat1/flux-proxy-L0im8J/local
```

I then started the main broker (using the command above).  Then I shelled into the cluster again, and to the same node and connected to the socket to verify three hosts were down.

```bash
export PYTHONPATH=$HOME/.local/lib/python3.6/site-packages
export PATH=/g/g0/sochat1/.local/bin:$PATH
cd /usr/workspace/sochat1/test-flux-burst/flux-burst-local/example
flux proxy local://./configs/run/local
```

You should see all the instances, that the main broker is online and the other nodes offline:

```bash
$ flux resource list
     STATE NNODES   NCORES NODELIST
      free      1       36 quartz8
 allocated      0        0
      down      3      108 quartz[9-11]
```

Now we want to test running a flux job and targeting the three down workers. Exit from the proxy so you again see that all four workers are free, and run the job to target them:

```bash
flux submit -N 3 --requires "not rank:0" /usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system
```

If you are watching the main broker still running, you should see the nodes join. But the problem now is that this command was run from the top level instance,
and not from inside of the burst. There might be a more clever way to run all of this, but the problem (as I see it) is that we are one level too low to control the bursting.
Hmm, can we do a flux proxy to the parent socket?

```bash
flux proxy flux submit -N 3 --requires "not rank:0" /usr/bin/flux start --broker-opts --config /usr/WS2/sochat1/test-flux-burst/flux-burst-local/example/configs/system
```
