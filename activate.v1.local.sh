# Run: source /data/home/cqm/Project/Code/chongqing/activate.v1.local.sh
# Legacy v1 EEG environment reconstructed from
# migration/chongqing-v1-requirements.lock.txt.
source /data/home/cqm/miniconda3/etc/profile.d/conda.sh
conda activate chongqing_v1
export PATH="/data/home/cqm/miniconda3/envs/chongqing_v1/bin:$PATH"
export CHONGQING_RAW_DATA_DIR=/data/home/cqm/Project/Dataset/Chongqing
export PYTHONPATH="/data/home/cqm/Project/Code/chongqing/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
cd /data/home/cqm/Project/Code/chongqing
