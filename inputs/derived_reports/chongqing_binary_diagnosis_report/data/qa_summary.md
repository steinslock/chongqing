# Chongqing Dataset QA Summary

- Clinical rows: 4610
- Clinical columns: 433
- Duplicate A ids: 0; duplicate L ids: 0
- diag3 counts: {'健康': 3126, '高危': 744, '多动症': 25, 'MDD': 490, '焦虑症': 57, '精分': 14, '-': 107, '双相': 9, '无基线信息，排除': 5, '孤独症': 1, 'PTSD': 8, '强迫症': 12, '品行障碍': 1, '抽动障碍': 2, '对立违抗': 9}
- label policies: {'primary_label_nonhealthy': {'negative_0': 3126, 'positive_1': 1372, 'excluded_null': 112}, 'sensitivity_label_clear_diagnosis': {'negative_0': 3126, 'positive_1': 628, 'excluded_null': 856}, 'sensitivity_label_mdd_highrisk': {'negative_0': 3126, 'positive_1': 1234, 'excluded_null': 250}}
- CDRS consistency: {'consistent_or_non_threshold_diag': 4498, 'missing_score': 107, 'excluded_with_score': 5}

## Modality coverage

- EEG: ids=2498, matched_subjects=2498, diag3={'健康': 1622, '高危': 445, 'MDD': 298, '焦虑症': 38, '-': 49, '精分': 9, '强迫症': 6, '多动症': 13, 'PTSD': 3, '品行障碍': 1, '双相': 6, '对立违抗': 6, '抽动障碍': 1, '无基线信息，排除': 1}
- fNIRS: ids=3367, matched_subjects=3284, diag3={'健康': 2054, '高危': 617, 'MDD': 410, '焦虑症': 53, '精分': 13, '-': 78, '强迫症': 9, '多动症': 21, 'PTSD': 5, '品行障碍': 1, '双相': 8, '抽动障碍': 2, '对立违抗': 9, '无基线信息，排除': 4}
- Eye_direct: ids=303, matched_subjects=291, diag3={'健康': 197, '高危': 50, 'MDD': 27, '焦虑症': 1, '-': 10, '精分': 1, '强迫症': 2, 'PTSD': 1, '多动症': 1, '双相': 1}
- Face: ids=4574, matched_subjects=4573, diag3={'健康': 3112, '高危': 737, '多动症': 25, 'MDD': 481, '焦虑症': 57, '精分': 14, '-': 100, '双相': 9, '无基线信息，排除': 5, '孤独症': 1, 'PTSD': 8, '强迫症': 12, '品行障碍': 1, '抽动障碍': 2, '对立违抗': 9}
- Eye_name_mapped: ids=871, matched_subjects=871, diag3={'健康': 556, 'MDD': 100, '高危': 169, '精分': 3, 'PTSD': 2, '-': 19, '强迫症': 1, '焦虑症': 13, '多动症': 5, '双相': 3}
