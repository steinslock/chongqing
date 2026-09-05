# Run: source /data/home/cqm/Project/Code/chongqing/activate.local.sh
# Existing Python 3.9 environment used for migration validation; not the
# original avmoe environment. See MIGRATION.md for full environment recovery.
source /data/home/cqm/miniconda3/etc/profile.d/conda.sh
conda activate M3DFEL
export PATH="/data/home/cqm/miniconda3/envs/M3DFEL/bin:$PATH"
export CHONGQING_RAW_DATA_DIR=/data/home/cqm/Project/Dataset/Chongqing
export PYTHONPATH="/data/home/cqm/Project/Code/chongqing/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
cd /data/home/cqm/Project/Code/chongqing
