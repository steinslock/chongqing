# 重庆多模态数据集健康/患病二分类诊断技术调查报告

生成日期：2026-07-03  
数据集：`/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`  
输出目录：`/home/qiangminc/codes/data4_qiangminc/outputs/chongqing_binary_diagnosis_report`

## 1. 技术摘要

本课题适合定义为“受试者级、多模态、缺失模态友好的健康/患病二分类诊断”。重庆数据集规模很大，临床主表提供了 4610 名受试者和 433 个字段，面部、近红外、脑电、眼动四类模态的覆盖率差异明显。基于当前本地盘点，最稳妥的第一阶段不是直接训练一个端到端多模态大模型，而是先建立受试者级 manifest、完成标签和数据泄漏控制、做单模态强基线，再用 late fusion 或 stacking 汇总各模态预测。

推荐的主标签为：

- `健康 = 0`
- `高危/MDD/焦虑症/多动症/双相/强迫症/PTSD/精分等非健康状态 = 1`
- 排除 `-` 和 `无基线信息，排除`

主标签下可用样本为 4498 人，其中健康 3126 人、患病/高危 1372 人、排除 112 人。考虑到“高危”与明确精神障碍诊断的边界不同，报告建议同时做两个敏感性分析：

- `明确诊断 vs 健康`：正类包括 MDD、焦虑症、多动症、双相、强迫症、PTSD、精分等，排除高危。
- `高危+MDD vs 健康`：只保留高危和 MDD 两个核心抑郁相关状态作为正类。

最重要的红线是避免临床量表泄漏。`诊断3-他评量表CDRS≥40` 已经以 CDRS 阈值参与标签定义，因此 CDRS、CES-DC、HAMA、自杀量表等临床量表不能作为多模态模型输入，只能用于标签定义、分层描述、临床基线对照或事后误差分析。

## 2. 已完成的数据盘点

本阶段只读扫描原始数据目录，并将派生索引写到数据集外部。已经生成的可复现文件如下：

- `../data/subject_manifest.csv`：受试者级索引，不包含姓名。
- `../data/modality_coverage.csv`：各模态覆盖统计。
- `../data/qa_summary.json` 和 `../data/qa_summary.md`：标签、覆盖率、对齐 QA 摘要。
- `../data/literature_matrix.csv`：25 篇论文/综述矩阵。

### 2.1 临床表和标签

临床文件为 `临床信息-重医6.3.xlsx`，主 sheet 为 `中小学复核问卷`。当前解析结果：

| 项目 | 结果 |
|---|---:|
| 受试者行数 | 4610 |
| 临床字段数 | 433 |
| A 编号重复 | 0 |
| L 编号重复 | 0 |
| 主标签可用样本 | 4498 |
| 主标签排除样本 | 112 |

`诊断3-他评量表CDRS≥40` 原始分布如下：

| 诊断3取值 | 人数 |
|---|---:|
| 健康 | 3126 |
| 高危 | 744 |
| MDD | 490 |
| 焦虑症 | 57 |
| 多动症 | 25 |
| 精分 | 14 |
| 强迫症 | 12 |
| 双相 | 9 |
| 对立违抗 | 9 |
| PTSD | 8 |
| 抽动障碍 | 2 |
| 孤独症 | 1 |
| 品行障碍 | 1 |
| `-` | 107 |
| 无基线信息，排除 | 5 |

标签策略建议：

| 标签版本 | 负类 | 正类 | 排除 | 用途 |
|---|---:|---:|---:|---|
| 主标签：非健康全阳性 | 3126 | 1372 | 112 | 主实验，最大化样本量，回答健康/患病二分类 |
| 敏感性1：明确诊断 vs 健康 | 3126 | 628 | 856 | 检验高危人群是否导致边界变模糊 |
| 敏感性2：高危+MDD vs 健康 | 3126 | 1234 | 250 | 更聚焦抑郁谱系和 CDRS 阈值 |

CDRS 一致性检查显示：4498 人与阈值定义或非阈值诊断逻辑一致，107 人缺失 CDRS 分数，5 人为“无基线信息，排除”。正式实验前应进一步抽查 CDRS 原始列、`诊断1/诊断2/诊断3` 的生成规则和任何人工复核备注。

### 2.2 模态覆盖

本地盘点显示，面部覆盖最完整，EEG 和 fNIRS 覆盖中等，眼动直接编号覆盖较小；眼动可借助网页日志姓名映射提升覆盖，但需要严格去重和人工抽查。

| 模态 | 可识别编号数 | 临床匹配人数 | 主要任务/来源 | 当前建议 |
|---|---:|---:|---|---|
| 面部 | 4574 | 4573 | 自我介绍、任务视频 | 主力模态之一，优先做统计特征基线 |
| fNIRS | 3367 | 3284 | 必可明、依瑞德设备 | 主力模态之一，需处理设备批次差异 |
| EEG | 2498 | 2498 | rest、oddball、1BACK | 主力模态之一，按任务分别建模 |
| 眼动直接编号 | 303 | 291 | 平滑追随、扫视、自由观看 | 可做高可信小样本基线 |
| 眼动姓名映射 | 871 | 871 | 网页日志辅助映射 | 只在完成冲突检查后进入主实验 |

任务级发现：

- EEG：`1_rest` 约 1334 人，`2_Oldball` 约 2358 人，`4_1BACK` 约 1810 人。
- fNIRS：`必可明近红外` 约 1391 个编号，`依瑞德近红外` 约 1977 个编号。
- 面部：`面部1-自我介绍1分钟` 约 4574 人，`面部2-任务` 约 4568 人。
- 眼动：平滑追随约 885 个目录，扫视约 850 个目录，自由观看约 846 个目录；直接编号匹配少，姓名映射潜力较大但风险也更高。

## 3. 研究问题定义

### 3.1 推荐的主问题

主问题应写成：

> 在不使用临床量表作为输入特征的前提下，利用 EEG、fNIRS、面部视频、眼动行为等客观多模态信号，建立受试者级模型区分健康与非健康/患病状态。

这个定义有三个好处：

- 与当前临床标签 `诊断3-他评量表CDRS≥40` 直接对齐。
- 保留“高危”人群，符合早筛场景。
- 允许缺失模态友好的训练和推理，不会把样本压缩到极少数完整四模态病例。

### 3.2 不建议的定义

不建议把任务直接写成“抑郁症 MDD vs 健康”的唯一主任务，因为当前标签中高危 744 人占比很大，完全排除会浪费大量早筛信息；也不建议把所有完整四模态病例作为唯一主分析，因为眼动完整覆盖少，会显著牺牲面部、EEG、fNIRS 的样本优势。

### 3.3 可扩展的副问题

正式论文或课题可以设置以下副问题：

- 单模态客观信号中，哪一种对主标签最有预测力？
- EEG 与 fNIRS 是否存在互补性？
- 面部与眼动是否能捕捉行为表达层面的互补信息？
- 高危样本是否处于健康与 MDD 之间的连续谱？
- 模型在性别、年龄、年级、学校/编号批次之间是否稳定？
- 缺失模态时，模型性能下降是否可控？

## 4. 文献调查矩阵

下表整理了 25 篇与本课题直接相关的论文或综述，覆盖 EEG、fNIRS、眼动、面部视频和多模态融合。它们共同给出的结论是：多模态融合通常能提升诊断性能，但可靠收益依赖于严格的受试者级划分、无泄漏特征、任务/设备批次控制、缺失模态处理和可解释性分析。

| # | 方向 | 文献 | 模态/方法 | 对本课题的启发 |
|---:|---|---|---|---|
| 1 | EEG+fNIRS+量表 | [Tang et al., A multimodal depression recognition method based on EEG-fNIRS-SDS](https://pubmed.ncbi.nlm.nih.gov/41617022/) | MI-WNet、自适应加权融合 | 可作为 v2 多模态加权融合参考；但本课题不能把参与标签定义的量表作为输入 |
| 2 | EEG+fNIRS | [Li Yi et al., Automatic depression diagnosis through hybrid EEG and near-infrared spectroscopy features using SVM](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1205931/full) | EEG/fNIRS 特征选择 + SVM | 直接支持 EEG+fNIRS 手工特征融合基线 |
| 3 | EEG+眼动 | [Yin et al., E2Mo: A Multimodal EEG-Eye Movement Model for Automatic Depression Detection](https://ojs.aaai.org/index.php/AAAI/article/view/37205) | 模态专家、mixture of modality experts | 适合启发缺失模态友好的专家融合 |
| 4 | EEG+眼动 | [Content-based multiple evidence fusion on EEG and eye movements](https://www.sciencedirect.com/science/article/abs/pii/S0169260722004813) | 决策层证据融合 | 支持先做 late fusion，再做更复杂中间融合 |
| 5 | EEG+瞳孔 | [Transformer-based fusion model for mild depression recognition with EEG and pupil area signals](https://pubmed.ncbi.nlm.nih.gov/39909988/) | CSP + Transformer | 可用于眼动瞳孔与 EEG 的中间融合探索 |
| 6 | EEG | [Cai et al., Feature-level fusion approaches based on multimodal EEG data](https://www.sciencedirect.com/science/article/pii/S1566253519302143) | 多任务/多刺激 EEG 特征级融合 | 启发 rest、oddball、1BACK 的任务内融合 |
| 7 | EEG | [Movahed et al., A major depressive disorder classification framework based on EEG signals](https://pubmed.ncbi.nlm.nih.gov/33957158/) | 统计、频谱、小波、连接、非线性特征 | 可作为 EEG v1 特征库模板 |
| 8 | EEG | [Rafiei et al., Automated Detection of MDD With EEG Signals](https://ieeexplore.ieee.org/document/9828387/) | InceptionTime | 适合作为 v2 深度时序模型 |
| 9 | EEG 综述 | [Liu et al., Machine learning approaches for diagnosing depression using EEG: A review](https://pmc.ncbi.nlm.nih.gov/articles/PMC9375981/) | EEG 机器学习综述 | 用于论证 EEG 特征族和验证风险 |
| 10 | 静息 EEG 综述 | [Lin et al., Resting-State EEG Depression Diagnosis](https://www.mdpi.com/1424-8220/24/21/6815) | 传统 ML 与深度学习综述 | 支持静息 EEG 作为解释性强的第一基线 |
| 11 | EEG CNN | [Resting-state EEG-based CNN for depression diagnosis and severity](https://pmc.ncbi.nlm.nih.gov/articles/PMC9589234/) | CNN | 提醒深度 EEG 在真实验证中性能可能并不夸张 |
| 12 | EEG 特征 | [Analysis of EEG features and automatic classification in first-episode MDD](https://pmc.ncbi.nlm.nih.gov/articles/PMC10644563/) | EEG 特征分析 + 分类 | 支持电生理指标解释和特征重要性分析 |
| 13 | 青少年 fNIRS | [fNIRS-Based characterization of adolescent depression using dynamic functional connectivity biomarkers](https://link.springer.com/article/10.1186/s12888-026-07799-3) | 青少年、VFT、动态功能连接 | 与本数据年龄段和 fNIRS 任务高度相关 |
| 14 | 青少年 fNIRS | [Classification of fNIRS signals from adolescents with MDD in suicide high- and low-risk groups](https://www.sciencedirect.com/science/article/pii/S0165032723009692) | 青少年 MDD、自杀风险、特征选择 | 支持前额叶 HbO/HbR 任务反应和连接特征 |
| 15 | fNIRS | [Zhong et al., Soft fusion of channel information in depression detection using fNIRS](https://pure.bit.edu.cn/en/publications/soft-fusion-of-channel-information-in-depression-detection-using-) | 通道选择、软融合 | 支持通道/脑区级融合，而不是盲目拼接所有通道 |
| 16 | fNIRS | [Zhu et al., Classifying MDD Using fNIRS During Motor Rehabilitation](https://ieeexplore.ieee.org/document/8986539) | 任务态 fNIRS 分类 | 支持跨任务 fNIRS 特征和鲁棒性检查 |
| 17 | fNIRS | [Identifying neuroimaging biomarkers of MDD from cortical hemodynamic responses](https://pmc.ncbi.nlm.nih.gov/articles/PMC9062667/) | fNIRS 生物标志物 | 支持通道重要性和生物标志物解释 |
| 18 | 眼动 | [Through the Youth Eyes: Training Depression Detection Algorithms with Eye Tracking Data](https://ieeexplore.ieee.org/document/10810399/) | 青少年眼动 + ML | 支持 fixation/saccade/blink/pupil 特征设计 |
| 19 | 眼动 | [Effective differentiation between depressed patients and controls using discriminative eye movement features](https://www.sciencedirect.com/science/article/abs/pii/S0165032722003251) | 三类基础眼动任务 | 与本数据平滑追随、扫视、自由观看直接对应 |
| 20 | 眼动 | [Diagnosing and tracking depression based on eye movement in response to VR](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2024.1280935/full) | fixation/saccade + XGBoost/MLP/SVM/RF | 可参考眼动特征组和交叉验证指标 |
| 21 | 面部+眼动 | [Stolicyn et al., Prediction of depression symptoms with face and eye movement tracking](https://www.cambridge.org/core/journals/psychological-medicine/article/prediction-of-depression-symptoms-in-individual-subjects-with-face-and-eye-movement-tracking/D3DD91C657FAB8C8676C0353750BC134) | 面部视频、眼动、ML | 支持面部行为和眼动行为的联合建模 |
| 22 | 面部视频 | [Pan et al., Spatial-Temporal Attention Network for Depression Recognition from Facial Videos](https://www.sciencedirect.com/science/article/abs/pii/S0957417423019127) | STA-DRN、时空注意力 | 可作为 v2 视频深度学习参考 |
| 23 | 面部视频 | [Depression recognition from facial videos: preprocessing and scheduling choices hide architectural contributions](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/ell2.12992) | 预处理和训练日程分析 | 强烈提醒报告帧采样、对齐、增强、划分策略 |
| 24 | 面部综述 | [Deep learning-based depression recognition through facial expression: A systematic review](https://www.sciencedirect.com/science/article/abs/pii/S0925231225002772) | 面部表情深度学习综述 | 用于定位面部视频研究和隐私伦理问题 |
| 25 | 广义多模态 | [Harnessing multimodal approaches for depression detection using LLMs](https://www.nature.com/articles/s44184-024-00112-8) | 文本、音频、视觉、LLM | 可作为未来引入语音/文本转录的背景，不建议作为当前主路线 |

## 5. 推荐建模路线

### 5.1 总体路线

建议分成两个版本推进：

**v1：单模态强基线 + late fusion/stacking。**  
目标是快速得到可信、可解释、可复现的结果。每个模态独立做特征提取、质量控制、模型训练和受试者级预测，再用 out-of-fold 预测分数、模态缺失 mask、年龄/性别/年级等非泄漏人口学变量训练二级融合模型。v1 是论文和课题开题最稳的主路线。

**v2：中间融合/Transformer/Mixture-of-Experts。**  
在 v1 的数据清洗、特征和划分稳定后，再探索 EEG+fNIRS、EEG+眼动、面部+眼动、多模态 Transformer、modality dropout、专家路由等方法。v2 应作为增强路线，而不是第一步的唯一赌注。

### 5.2 EEG

EEG 数据以 BDF 为主，建议用 MNE 建立统一读取和预处理流程。按任务分别处理 `rest`、`oddball`、`1BACK`，不要把不同任务无标记地混在一起。

推荐预处理：

- 读取 BDF，统一通道名、采样率、参考方式和 montage。
- 带通滤波，例如 0.5-45 Hz；保留工频 notch。
- 自动检测坏道、高振幅片段、平坦片段和眼动/肌电污染。
- ICA 或 ASR 等方法清除眼动和肌电伪迹，保留 QC 指标。
- 所有窗口切分必须在受试者内部完成，训练/验证/测试按受试者划分。

推荐特征：

- 频带功率：delta、theta、alpha、beta、gamma 的绝对功率和相对功率。
- 额叶 alpha 不对称、左右半球不对称、前后区域比值。
- 功能连接：coherence、PLI/wPLI、PLV、相位-幅度相关等。
- 非线性特征：样本熵、近似熵、Higuchi fractal dimension、Lempel-Ziv complexity。
- 小波/时频特征：任务态或事件相关窗口的能量变化。
- ERP：oddball 的 P300、N2 振幅和潜伏期；1BACK 的工作记忆相关成分。

推荐模型：

- v1：Elastic Net logistic regression、SVM、Random Forest、LightGBM/XGBoost。
- v1 解释：permutation importance、SHAP、区域级特征重要性。
- v2：EEGNet、InceptionTime、1D CNN、时频图 CNN、Transformer。

### 5.3 fNIRS

fNIRS 数据存在至少两类设备来源，必须把设备差异作为批次风险处理。建议先按设备分别跑 QC 和基线，再做合并模型。

推荐预处理：

- 读取 `.nirs`、`.wl1/.wl2` 或导出格式，统一通道、源探距离、采样率和任务事件。
- 光密度转换、运动伪迹校正、带通滤波。
- 转换 HbO、HbR、HbT。
- 标注短通道或质量差通道；若无短通道，至少记录信噪比和运动伪迹比例。

推荐特征：

- 任务 GLM beta：每个任务条件下 HbO/HbR/HbT 的 beta。
- 统计响应：均值、峰值、峰值时间、斜率、面积、恢复时间。
- 静息/任务功能连接：相关、偏相关、动态功能连接。
- 频域特征：fALFF、低频功率。
- 非线性特征：样本熵、复杂度。
- 脑区聚合：通道级特征再聚合到前额叶/颞叶/左右半球区域。

推荐模型：

- v1：LightGBM、SVM、Elastic Net、Random Forest。
- 设备控制：模型中加入设备 indicator、分设备评估、设备留一验证。
- v2：通道注意力、图神经网络、软通道融合、动态连接网络。

### 5.4 面部视频

面部视频覆盖几乎完整，是最适合先做大样本行为表型基线的模态。建议先用 OpenFace 或 MediaPipe 提取结构化特征，而不是一开始训练视频大模型。

推荐预处理：

- 视频读取，抽帧，检测人脸，记录检测成功率。
- 估计 landmark、头姿、视线、眼睑开合、嘴部运动和 AU。
- 对每个视频生成 QC：有效帧比例、遮挡比例、头部偏转比例、光照异常、帧率。
- `自我介绍` 和 `任务视频` 分别建模，再做任务级融合。

推荐特征：

- AU 强度和出现频率：均值、标准差、分位数、峰值、持续时间。
- 表情动态：微笑频率、嘴角活动、眉眼活动、表达丰富度。
- 头姿：pitch/yaw/roll 的均值、波动、极值和运动速度。
- 眼部行为：眨眼频率、眼睑开合、视线偏移。
- 情绪概率：若使用表情识别模型，只作为行为特征，避免把模型输出当作临床真值。
- 时序摘要：滑窗统计、变化率、低活动时长、任务前后差异。

推荐模型：

- v1：LightGBM、Elastic Net、SVM、CatBoost。
- v2：VideoMAE、TimeSformer、3D CNN、STA-DRN 风格时空注意力模型。
- 注意：面部深度学习极易受预处理、帧采样、增强和划分方式影响，必须完整报告实验设置。

### 5.5 眼动

眼动数据应分成两个可信度等级。直接编号匹配样本可以立即做小样本基线；姓名/网页日志辅助映射样本需要重复名、冲突名和时间戳人工抽查后才能进入主分析。

推荐特征：

- fixation：数量、平均时长、总时长、空间分布、离散度。
- saccade：数量、幅度、峰速度、平均速度、潜伏期、方向分布。
- smooth pursuit：追踪误差、速度增益、丢失追踪比例。
- blink：频率、持续时间、任务阶段分布。
- pupil：均值、变异、反应幅度、低频波动。
- free-viewing：AOI 注视比例、转移矩阵、扫描路径长度、熵。

推荐模型：

- v1：Logistic regression、SVM、Random Forest、LightGBM。
- v1 先按任务分别建模，再融合三类眼动任务。
- v2：眼动序列 Transformer、scanpath embedding、EEG+眼动专家融合。

## 6. 多模态融合策略

### 6.1 为什么 v1 选择 late fusion

本数据集中四个模态覆盖差异很大。如果只使用四模态完整病例，样本量会被眼动覆盖限制，且容易产生选择偏倚。late fusion/stacking 能让每个模态利用自己的最大可用样本，并在融合阶段显式处理缺失。

### 6.2 v1 融合流程

推荐流程：

1. 固定受试者级 K 折划分，并保存 split 文件。
2. 每个模态在训练折内完成预处理参数拟合、特征选择和模型选择。
3. 生成每个受试者的 out-of-fold 预测分数。
4. 融合模型输入包括：各模态预测分数、各模态是否可用的 mask、年龄/性别/年级等非泄漏变量。
5. 融合模型使用简单可解释模型起步，例如 Logistic regression、Elastic Net、LightGBM。
6. 在独立测试折上报告单模态和融合模型的同一组指标。

### 6.3 v2 融合方向

当 v1 稳定后，可探索：

- EEG+fNIRS：脑电神经活动和血氧动力学互补，适合中间融合。
- EEG+眼动：认知控制、注意和生理反应互补，适合 modality expert。
- 面部+眼动：行为表达和视觉注意互补，适合任务级行为融合。
- 全模态 MoE：每个模态一个专家，路由网络根据可用模态和质量指标加权。
- modality dropout：训练时随机遮挡模态，提高推理时缺失模态鲁棒性。

## 7. 实验设计与评估

### 7.1 数据划分

所有实验必须按受试者级划分。任何窗口、帧、epoch、trial 都不能让同一受试者同时出现在训练集和测试集。

建议三层划分：

- 主报告：5 折或 10 折 stratified group cross-validation。
- 模型选择：训练折内部 nested CV 或固定 validation split。
- 外推验证：若编号前缀可近似代表学校/批次，可做学校/编号前缀留一或分组 holdout。

### 7.2 指标

主指标：

- AUROC
- AUPRC
- balanced accuracy
- sensitivity/recall
- specificity
- F1
- calibration curve 和 Brier score
- bootstrap 95% confidence interval

不建议只报告 accuracy。当前健康/正类比例约为 3126:1372，accuracy 容易掩盖正类召回不足。若用于筛查，需重点报告 sensitivity，并在固定 specificity 下比较模型。

### 7.3 类别不平衡

训练阶段可以使用 class weight、balanced sampler 或阈值调优；验证和测试集不能过采样。阈值应在训练/验证数据上预先确定，例如 Youden index、固定 sensitivity 或固定 specificity，然后锁定到测试集。

### 7.4 消融实验

建议至少报告：

- 单模态：EEG、fNIRS、面部、眼动。
- 任务消融：rest/oddball/1BACK，自我介绍/任务视频，平滑追随/扫视/自由观看。
- 融合消融：无 mask、加 mask、加人口学变量、加质量指标。
- 标签消融：主标签、明确诊断 vs 健康、高危+MDD vs 健康。
- 批次消融：分设备、分学校/编号前缀、分年龄/性别/年级。

## 8. 数据泄漏、伦理和隐私风险

### 8.1 数据泄漏

必须禁止以下特征进入模型：

- CDRS 原始分数和所有 CDRS 派生字段。
- CES-DC、HAMA、自杀量表等高度相关临床量表。
- 任何直接诊断字段、人工复核字段、病程/用药等只在病例中记录的临床字段。
- 姓名、身份证、电话、学校班级等身份识别字段。
- 采集后处理产生、但与标签或分组直接绑定的文件名/目录名。

可作为协变量或分层变量的字段：

- 年龄、性别、年级。
- 设备型号、任务类型、采集批次。
- 模态质量指标，例如有效帧比例、坏道比例、可用 trial 数。

### 8.2 隐私与伦理

该数据包含未成年人、多模态生理信号、面部视频和精神健康标签，属于高敏感数据。建议：

- 所有公开报告只使用匿名编号，不输出姓名。
- 模型训练日志不保存可逆身份信息。
- 视频和原始脑电/近红外/眼动数据只在授权环境内处理。
- 发表论文时只报告聚合统计和匿名化示例。
- 对性别、年龄、年级等子群体做公平性和误差分析。
- 明确模型用途是辅助筛查/科研分析，不是独立临床诊断。

## 9. 阶段性实施路线

### Phase 0：索引和 QA

当前已完成第一版：

- 建立 `subject_manifest.csv`。
- 复现 `诊断3` 计数和三套标签。
- 统计四个模态覆盖。
- 建立文献矩阵。
- 生成数据集外部 QA 文件。

下一步应补充：

- 将 split 文件固化，例如 `splits/primary_5fold_seed20260703.csv`。
- 对眼动姓名映射做重复名和冲突名人工抽查。
- 抽查每个模态 20-50 个文件，确认任务事件和文件格式。

### Phase 1：单模态特征工程

优先级建议：

1. 面部：覆盖最大，先提 OpenFace/MediaPipe 结构化特征。
2. EEG：按 rest、oddball、1BACK 提取 hand-crafted EEG 特征。
3. fNIRS：按设备分别提 HbO/HbR/HbT 和 GLM/连接特征。
4. 眼动：先使用直接编号样本，姓名映射样本通过 QA 后加入。

输出应为每个模态一张受试者级特征表：

- `features_face_subject.csv`
- `features_eeg_subject.csv`
- `features_fnirs_subject.csv`
- `features_eye_subject_direct.csv`
- `features_eye_subject_name_mapped_qc.csv`

### Phase 2：单模态基线

每个模态都训练相同模型族，便于比较：

- Logistic regression / Elastic Net
- SVM
- Random Forest
- LightGBM 或 XGBoost

每个模型报告：

- 主标签性能。
- 两个敏感性标签性能。
- 年龄/性别/年级分层性能。
- 特征重要性或区域/任务重要性。

### Phase 3：融合模型

完成单模态基线后训练：

- 单模态预测分数 stacking。
- 带缺失模态 mask 的 stacking。
- 加质量指标的 stacking。
- 与 complete-case 四模态融合对比，但 complete-case 只作为消融，不作为唯一主结果。

### Phase 4：论文级分析

最终论文或项目报告应包含：

- 预注册式标签和排除规则。
- 数据流图和样本流图。
- 单模态与多模态性能表。
- ROC/PR 曲线和校准曲线。
- 子群体公平性分析。
- 错误案例分析。
- 数据泄漏和伦理控制说明。

## 10. 建议的目录结构

所有派生文件都应放在数据集外部：

```text
outputs/inputs/derived_reports/chongqing_binary_diagnosis_report/
  data/
    subject_manifest.csv
    modality_coverage.csv
    qa_summary.json
    qa_summary.md
    literature_matrix.csv
  scripts/
    build_manifest.py
  report/
    chongqing_binary_diagnosis_survey.md
  splits/
    primary_5fold_seed20260703.csv
  features/
    face/
    eeg/
    fnirs/
    eye/
  models/
    baseline/
    fusion/
  figures/
```

原始目录 `/datasets_qiangmin/chongqing` 应保持只读。派生特征、缓存、中间模型和报告均不得写回原始数据集。

## 11. 结论

这份数据集最有价值的策略是“充分利用大样本模态，不被小样本完整多模态束缚”。主实验应以受试者级 `健康 vs 非健康` 为目标，使用面部、EEG、fNIRS 作为三大主模态，眼动作为高价值但需严谨对齐的补充模态。第一篇课题成果最稳的路线是：

1. 建立可复现 manifest 和标签规则。
2. 提取各模态可解释统计特征。
3. 完成单模态强基线。
4. 使用 late fusion/stacking 做缺失模态友好的多模态诊断。
5. 用敏感性标签、批次外推、子群体评估和校准分析证明结论稳健。

若 v1 结果清楚，再推进 EEG+fNIRS、EEG+眼动、面部+眼动和全模态 MoE/Transformer。这样既能快速产出可靠结果，也给后续深度模型留下足够空间。

