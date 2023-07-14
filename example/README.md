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
# Ensure the installed executable is on your path
export PATH=$HOME/.local/bin:$PATH

# If you are using a custom flux install
$ python burst-slurm-allocation.py --config-dir ./configs --flux-root /path/to/flux/root --network-device eno1

# If you want to discover flux on your path
$ python burst-slurm-allocation.py --config-dir ./configs --network-device eno1

# Development with one node (e.g., DevContainer)
$ python3 burst-slurm-allocation.py --config-dir ./configs --network-device eno1 --hostnames $(hostname)
```
```
🌳️ Flux root set to /usr
🦩️ Writing flux config to /workspaces/flux-burst-local/example/configs/system/system.toml
🌀️ Done! Use the following command to start your Flux instance and burst!
    It is also written to /workspaces/flux-burst-local/example/configs/start.sh

/usr/bin/flux start --broker-opts --config /workspaces/flux-burst-local/example/configs -Stbon.fanout=256 -Srundir=/workspaces/flux-burst-local/example/configs/run -Sstatedir=/workspaces/flux-burst-local/example/configs/run -Slocal-uri=local:///workspaces/flux-burst-local/example/configs/run/local -Slog-stderr-level=7 -Slog-stderr-mode=local /home/vscode/.local/bin/flux-burst-local --config-dir /workspaces/flux-burst-local/example/configs --flux-root /usr
```
The above script is going to setup the configs and give you a command that will use them
to start a flux instance, and then also start a more standard flux burst plugin flow (with the same
local configs) so you can burst to local instances. Note that the flux root should have lib, bin, libexec, etc. in it. It's the `--prefix`
you chose for the install. Here is what the generated tree looks like under configs:

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

I wasn't able to get an allocation so I'll develop this tomorrow.
