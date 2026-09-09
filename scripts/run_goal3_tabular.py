#!/usr/bin/env python
"""Cross-fit the Goal 3 tabular comparators.

Demographics and the Goal 2.8 traditional 321-feature block pass through the
same inner splits as the deep model, producing one scalar each. Q2 then compares
two scalars rather than one scalar against a 321-column block, and the increment
test cannot be decided by dimensionality.

Depends only on the splits and the Goal 2.8 feature tables, so it runs before
and independently of any deep training.
"""

from __future__ import annotations

import argparse
import json

from joblib import Parallel, delayed

from chongqing_binary.goal3.config import ensure_output, load_goal_config
from chongqing_binary.goal3.protocol import load_cohort
from chongqing_binary.goal3.runner import tabular_path, tabular_scores


def _one(config_path: str, protocol: str, seed: int, n_jobs: int, overwrite: bool) -> str:
    config = load_goal_config(config_path)
    path = tabular_path(config, protocol, seed)
    if path.exists() and not overwrite:
        return f"skip {path.name}"
    cohort = load_cohort(config)
    payload = tabular_scores(config, cohort, protocol, seed, n_jobs=n_jobs)
    ensure_output(path, config).write_text(json.dumps(payload), encoding="utf-8")
    chosen = {k: (v["demo_model"], v["trad_model"]) for k, v in payload["folds"].items()}
    return f"wrote {path.name} chosen={chosen}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--model-n-jobs", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    config = load_goal_config(args.config)
    jobs = [(protocol, seed)
            for protocol in config["protocol"]["cv_protocols"]
            for seed in config["deep"]["seeds"]]
    results = Parallel(n_jobs=args.workers, backend="loky", verbose=5)(
        delayed(_one)(args.config, protocol, seed, args.model_n_jobs, args.overwrite)
        for protocol, seed in jobs
    )
    for line in results:
        print(line)


if __name__ == "__main__":
    main()
