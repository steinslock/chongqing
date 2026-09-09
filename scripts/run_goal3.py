#!/usr/bin/env python
"""Goal 3 deep model matrix.

One job is (configuration, cv_protocol, seed) and writes its own file, so a run
is restartable. The configurations are the closed set declared in
`reports/goal3_method_design.md`; nothing is added after results are seen.
"""

from __future__ import annotations

import argparse
import traceback

from joblib import Parallel, delayed

from chongqing_binary.goal3.config import load_goal_config
from chongqing_binary.goal3.runner import (
    Configuration,
    declared_configurations,
    job_output_path,
    run_deep_job,
    write_job,
)


def _one(config_path: str, configuration: Configuration, protocol: str, seed: int,
         overwrite: bool, min_free_mb: int, torch_threads: int,
         cache_dir: str | None) -> str:
    # Without this, every worker's torch grabs all 192 cores and the workers
    # fight each other: measured on this host, EEGNet runs at 180 ms/step on 4
    # threads and 438 ms/step on 8. Affects speed only, never a fit.
    import torch

    torch.set_num_threads(max(1, torch_threads))
    config = load_goal_config(config_path)
    if cache_dir:
        # A RAM-backed copy of the trial cache. The host's shared filesystem was
        # the bottleneck under load: workers sat in uninterruptible disk wait
        # while a third of the cores were idle. Same bytes, different location.
        config["paths"]["trial_cache_dir"] = cache_dir
    path = job_output_path(config, configuration, protocol, seed, "label")
    if path.exists() and not overwrite:
        return f"skip {path.name}"
    try:
        result = run_deep_job(
            config, configuration, protocol, seed, min_free_mb=min_free_mb,
            dump_embeddings=(configuration.arm == "confirmatory"),
        )
        write_job(config, result, path)
        return f"done {path.name} rows={len(result['predictions'])}"
    except Exception:  # noqa: BLE001
        return f"FAILED {path.name}\n{traceback.format_exc()}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--arms", nargs="*", default=None,
                        help="restrict to these arms, e.g. confirmatory")
    parser.add_argument("--configs", nargs="*", default=None, help="restrict to these config ids")
    parser.add_argument("--encoders", nargs="*", default=None, help="restrict to these encoders")
    parser.add_argument("--exclude-encoders", nargs="*", default=None,
                        help="skip these encoders, so a memory-hungry one can run at lower concurrency")
    parser.add_argument("--protocols", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--cache-dir", default=None,
                        help="override the trial cache location, e.g. a /dev/shm staging copy")
    parser.add_argument("--torch-threads", type=int, default=4,
                        help="CPU threads per worker; keep workers x threads under the core count")
    args = parser.parse_args()

    config = load_goal_config(args.config)
    protocols = args.protocols or list(config["protocol"]["cv_protocols"])
    seeds = args.seeds if args.seeds is not None else list(config["deep"]["seeds"])
    configurations = declared_configurations()
    if args.arms:
        configurations = [c for c in configurations if c.arm in set(args.arms)]
    if args.configs:
        configurations = [c for c in configurations if c.config_id in set(args.configs)]
    if args.encoders:
        configurations = [c for c in configurations if c.encoder in set(args.encoders)]
    if args.exclude_encoders:
        configurations = [c for c in configurations if c.encoder not in set(args.exclude_encoders)]

    jobs = [(c, p, s) for c in configurations for p in protocols for s in seeds]
    print(f"[goal3] {len(jobs)} jobs, {args.workers} workers", flush=True)
    results = Parallel(n_jobs=args.workers, backend="loky", verbose=10)(
        delayed(_one)(args.config, c, p, s, args.overwrite, int(config["deep"]["min_free_mb"]),
                      args.torch_threads, args.cache_dir)
        for c, p, s in jobs
    )
    for line in results:
        print(line, flush=True)


if __name__ == "__main__":
    main()
