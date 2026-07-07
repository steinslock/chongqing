# Chongqing v1 Single-Modality Baselines

This project contains reproducible single-modality baselines for the Chongqing health/disease binary diagnosis task.

First milestone:

```bash
source /home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/activate
cd /home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1
python eeg/scripts/index_eeg_files.py --task rest
python eeg/scripts/extract_rest_features.py --task rest --n-jobs 4
python eeg/scripts/train_rest_baseline.py --label primary_label_nonhealthy
```

For smoke tests, add `--limit 5` to each script.

EEG deep baselines:

```bash
source /home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/activate
cd /home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1

python eeg/scripts/cache_deep_windows.py --task rest
python eeg/scripts/cache_deep_windows.py --task oddball
python eeg/scripts/cache_deep_windows.py --task 1back

python eeg/scripts/train_deep_eeg.py --task rest --model eegnet --device cuda:0
python eeg/scripts/train_deep_eeg.py --task rest --model inceptiontime --device cuda:1
python eeg/scripts/train_deep_eeg.py --task oddball --model eegnet --device cuda:0
python eeg/scripts/train_deep_eeg.py --task oddball --model inceptiontime --device cuda:1
python eeg/scripts/train_deep_eeg.py --task 1back --model eegnet --device cuda:0
python eeg/scripts/train_deep_eeg.py --task 1back --model inceptiontime --device cuda:1

python eeg/scripts/summarize_deep_baselines.py
```

Deep smoke tests:

```bash
python eeg/scripts/cache_deep_windows.py --task rest --limit-subjects 8 --max-windows-per-subject 2
python eeg/scripts/train_deep_eeg.py --task rest --model eegnet --epochs 1 --folds 2 --limit-subjects 32 --batch-size 16 --num-workers 0
```

Raw data stays read-only. Generated files are written only under this v1 directory.
