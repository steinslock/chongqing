# Run: source /data/home/cqm/Project/Code/chongqing/activate.local.sh
# Single unified project environment (chongqing_v1), reconstructed from
# migration/chongqing-v1-requirements.lock.txt.
# Carries MNE, OpenCV, torch/torchvision, scikit-learn, scipy and openpyxl,
# so EEG, fNIRS, Face and spreadsheet work all run here.
source /data/home/cqm/miniconda3/etc/profile.d/conda.sh
conda activate chongqing_v1
export PATH="/data/home/cqm/miniconda3/envs/chongqing_v1/bin:$PATH"
export CHONGQING_RAW_DATA_DIR=/data/home/cqm/Project/Dataset/Chongqing
export PYTHONPATH="/data/home/cqm/Project/Code/chongqing/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
cd /data/home/cqm/Project/Code/chongqing
