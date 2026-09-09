# Goal 2.10 眼动模态：文献调研与方法设计（实施前）

日期：2026-09-08
状态：**设计文档**。本文不产出任何模型结果，只确定"做什么、为什么这么做、预期是什么"。

实施进度：第 1 步（就绪审计）已完成，见 `reports/eye_readiness_audit.md` 与
`PROGRESS.md` 的 2026-09-08 条目。审计对本文的两处修正记在 §4.6 与 §4.7 之后的
"审计回填"一节，原文不删改，以便对照事先预期与事后事实。

本文分四部分：一、已核实的数据事实；二、文献调研结论；三、文献方法与我们数据的逐条匹配；
四、建议的方法与实施计划。

---

## 一、已核实的数据事实

以下全部由本次直接读取原始文件得到，不依赖 `data_audit.md` 的既有记录。

### 1.1 三个设备，三份几乎不相交的队列

| 来源 | 路径 | 采样率 | 唯一 A_id | 落在 manifest | 落在 CV |
|---|---|---|---|---|---|
| `qixin_120` | `眼动/七鑫易维原始工程/眼动` | 120 Hz | 432 | 426 | 336 |
| `qixin_500` | `眼动/七鑫易维原始工程/眼动-F500` | 500 Hz | 420 | 405 | 331 |
| `tobii` | `眼动/Tobbi原始数据` | 60 Hz | 337 | 329 | 253 |
| 合计（去重） | | | 1187 | 1158 | **919** |

同时出现在两个设备的被试只有 **2 人**。设备与采集点几乎完全共线：

- `qixin_120` 独占 B14 / B15 / B16 / C02 / C17 / C18 / D08；
- `qixin_500` 独占 A04 / A10 / B01 / B03 / B05 / D13 / E06；
- `tobii` 与 `qixin_500` 覆盖同一批学校，但是**不同的人**；
- 只有 A02 与 E16 两个前缀同时出现三种设备。

这与 fNIRS 的 Yiruid/Bikom 是同一类问题，处理方式必须一致：**分设备建模，禁止跨设备合并原始特征**。

### 1.2 `has_eye_direct = 291` 是低估

manifest 里的眼动覆盖是用 `L\d+` 正则从路径里提取的（`src/chongqing_binary/audit.py:_extract_l_ids`），
而眼动文件名带的是 `A_id`（`A02062_<name>_251105161924`、`眼动-tobbi E16284<name>_free.xlsx`），
不是 `L_id`。改用 `A_id` 键后 CV 内可用被试从 291 变成 **919**，是 EEG（2498）与 fNIRS（3284）之外
第三大的模态，且与它们高度重叠（眼动被试中约 80% 有 EEG、约 95% 有 fNIRS、约 99% 有面部）。

### 1.3 三个任务，范式结构完整可复原

`附件/` 里**没有**眼动范式脚本。但范式可以从两处复原，且两处一致：

- 七鑫易维工程文件 `眼动.asdata` / `眼动-F500.asdata`（JSON），
  `experimentPoMap[*].recordPoMap[*].mediaInRecordMap` 给出每个被试每个刺激的
  `startTime` / `endTime`（ms）；
- Tobii Pro Lab 导出的 xlsx，逐采样点带 `Presented Stimulus name`、`Event`
  （`ImageStimulusStart` / `VideoStimulusStart`）。

复原结果：

**自由观看**（`free_viewing`）
- 36 个刺激试次，每试次 = 中央十字 1.0 s → 人脸 4.0 s → 空白 1.0 s；
- 刺激为 CFAPS 风格的单张灰度正面人脸，黑底居中，1920×1080；
- 效价与性别完全平衡：`HF`×6、`HM`×6、`NEF`×6、`NEM`×6、`SAF`×6、`SAM`×6
  （高兴 12、中性 12、悲伤 12；男女各 18）；
- 顺序固定，所有被试相同（`1-NEF15, 2-SAM13, 3-NEM44, …, 36-NEM99`）；
- 七鑫易维 429/444（`眼动`）与 392/398（`眼动-F500`）的记录含完整 110 段时间线。

**扫视**（`saccade`）
- 前扫视说明 → 练习 10 s → 正式 **20 s** → 反扫视说明 → 练习 10 s → 正式 **20 s**；
- 刺激是 1920×1080 / 60 fps 的 mp4，两个工程下的视频文件字节大小一致，即同一套刺激；
- 429/440 与 406/408 的记录含完整 10 段时间线。

**平滑追随**（`smooth_pursuit`）
- 说明 → 追随视频 **135.9 s**（8160 帧 / 60 fps），单一刺激。

### 1.4 可用的原始量

- 七鑫易维每被试目录：`_basic.csv`（双眼注视点 x/y/z、瞳孔中心、瞳孔直径 px 与 **mm**、
  逐眼 blink 标志、`timestampUs`）、`_filter.csv`（厂商 I-DT 事件表：注视/扫视分段、
  `centerX/Y`、`duration`、双眼瞳孔 mm）、`_blink*.csv`、`_velocity.csv`、`_index.csv`；
  `_annotation.csv` **是空的**（只有表头），所以刺激对齐必须走 `.asdata`。
- `.asdata` 的 `record` 节点还直接给出 QC：`validRatio`、`gazeRate`、`leftScore`/`rightScore`、
  `fixationCount`、`saccadeCount`、`blinkCount`、`duration`。
- Tobii xlsx：96 列，含 Tobii I-VT 的逐采样点 `Eye movement type`
  （Fixation / Saccade / EyesNotFound / Unclassified）、`Eye movement event duration`、
  `Fixation point X/Y`、左右瞳孔直径、`Validity left/right`，以及**每次录制的标定质量**
  （`Average calibration accuracy (degrees)` 等 18 列）。

### 1.5 已知的数据缺陷

- 同一被试同一任务存在多份录制：`qixin_120` 21/7/19 例，`qixin_500` 11/20/7 例，合计约 85 人次。需要去重规则。
- 约 29 个目录/文件名没有 `A_id`（`User1_251028130305`、`<name>_251022130431`、
  `C17049-<name>`、`B16072--_<name>`、Tobii 的 `Recording8.xlsx` 等）。计划记录并排除，不做姓名映射。
- Tobii 有 2 个文件拼写为 `_sacaade.xlsx`。

---

## 二、文献调研结论

### 2.1 自由观看 / 情绪面孔：效应最稳，但只在特定指标上

2023 年的元分析（14 研究、474 抑郁 / 693 对照）给出：

| 指标 | 正性刺激 | 负性刺激 | 中性刺激 |
|---|---|---|---|
| 注视总时长 fixation duration | SMD **−0.71** [−1.20, −0.23] | SMD **+0.59** [0.27, 0.91] | +0.02 [−0.20, 0.24]，**不显著** |
| 注视次数 fixation count | SMD **−0.87** [−1.21, −0.54] | SMD **+0.32** [0.09, 0.54] | −0.13，**不显著** |
| 首次注视时长 first fixation duration | −0.39，不显著 | −0.10，不显著 | +0.35，不显著 |

三点必须记住：

1. **中性条件是零效应**。这不是噪声，是这套理论的内部对照：抑郁改变的是对情绪信息的
   维持性注意，不是整体注视行为。因此**效价对照（正性−中性、负性−中性）才是正确的特征**，
   而不是原始注视时长。这一点恰好与本项目在面部模态上的做法一致。
2. **早期指向（first fixation）没有效应，维持性注意才有**。所以试次内应该切"晚窗"。
3. 异质性极高（I² = 87–89%），且刺激呈现时长多为 8–10 s。

### 2.2 但"偏向分数"本身的信度是个已知问题

- 点探测任务的偏向差值分数在 9600 人的评估中，36 种变体**没有一种**内部信度足以支撑
  个体差异分析；
- 眼动的重测信度混杂，ICC 从 −0.31 到 0.71；
- 但同一批工作也发现：**8 s 自由观看的原始 dwell time 与注视次数内部一致性是"中等到优秀"的**，
  塌掉的是**差值分数**。

结论：不要只提交差值分数。要**同时**提交各效价的绝对指标和少量对照量，并且**为每个特征
报告分半信度**，把信度不足的特征标出来。

### 2.3 反扫视：有效应，但和年龄强烈共线

- 抑郁组反扫视错误率更高、潜伏期更长，这是重复过的；
- 但反扫视错误率在发育上随年龄快速下降，约 **14–15 岁进入平台**；15 岁以下的潜伏期与
  方向性错误都显著高于 15 岁以上。

我们的队列是 **9–20 岁**，而 `demographics` 基线（age+sex+grade）在全体 3597 人上已经达到
0.643–0.671。**反扫视错误率的大部分方差会被年龄吸收**。这是一个可以事先写下的预测。

### 2.4 平滑追随与自由观看的"全局"指标

- MDD 自由观看的 **scanpath 长度显著缩短**（d = 0.60–0.77，判别准确率 72.1%）；
- 平滑追随中 MDD **扫视时长更长、扫视峰速更低**（AUC = 0.76），解释为用追赶扫视补偿位置误差；
- 注视稳定性任务无组间差异。
- 平滑追随的标准量化：速度增益（眼速/靶速的时间加权比）、位置 RMSE、追赶扫视频率
  （方向落在靶运动方向 ±45°、幅度 ≥1.5° 的扫视）。

### 2.5 瞳孔

- 抑郁者对负性/烦躁刺激的**维持性瞳孔扩张更大**；
- 奖赏预期时瞳孔扩张减弱，且与快感缺失相关，2023 年有独立重复；
- 青少年样本中，对悲伤刺激扩张更大者抑郁风险更高。
- 我们两套设备都记录了**毫米单位**的瞳孔直径，且自由观看每试次前有 1 s 中央十字可作基线。

### 2.6 机器学习类工作：区分"能学的"和"不能学的"

**值得参照的**（npj Digital Medicine 2026，126 名年轻成人，500 Hz，句子阅读范式）：
- 嵌套 5 折、被试不跨折、按性别与组别分层；
- 排除数据质量差的被试（6 例缺失 + 13 例数据丢失 ≥50%）；
- 临床 vs 对照 AUC = 0.793 [0.766, 0.819]；抑郁 vs 自杀意念只有 0.609；
- 作者自己指出特异度只有 0.674，且**模型部分解码的是作答偏好而不是纯注意模式**。

**不值得参照的**（IJMCNM 2024，扫描路径图 + ResNet）：
- 总共 60 张扫描路径图，图像增强到 600，然后**按图像随机 80/20 划分**——被试级泄漏几乎必然；
- 三分类平均准确率 48%。这是本项目 `EXPERIMENT_PROTOCOL.md` 明令禁止的做法，列为反例。

**最接近我们决策规则的**（Frontiers in Neurology 2025，93 人，10–25 岁，六个眼动范式）：
- 基线 = 人口学 + BPRS + MADRS + YMRS，AUC **0.571**；加入眼动后 **0.679**，声称提升 18.9%。
- 但基线的 95% CI 是 **[0.143, 0.964]**。一个 CI 跨越 0.5 的基线不是基线。
  这与 Goal 2.9 撤回的那个阳性结果是**同一个错误**：赢一个本身不高于随机的比较者。
  我们的规则（`comparator_above_chance`）会直接拒绝这个结果。

VR 那篇 86% 准确率的研究用的正是 **七鑫易维（7invensun）** 的设备，样本 69 人、单中心、无外部验证，
不能作为效应量预期。

### 2.7 数据质量是个真实的混杂

眼动数据质量的系统性差异会被误读成组间差异，这是该领域的公认问题；且**采集质量本身随人群变化**
（年龄、族裔都被证明影响精度）。我们三套设备的采样率、标定流程、采集点都不同，
`validRatio` 与标定精度必须进 QC 特征集，并且必须跑 `signal_qc vs qc` 对照。

---

## 三、文献方法与我们数据的逐条匹配

| 文献做法 | 我们能否复现 | 说明 |
|---|---|---|
| 情绪面孔自由观看的效价对照 | **能，且设计更干净** | 36 试次、效价与性别完全平衡、顺序固定。中性条件可作为被试内基线 |
| 8–10 s 呈现时长 | **不能，只有 4 s** | 维持性注意窗被压缩。缓解：切早窗 0–1 s / 晚窗 1–4 s，晚窗对应"维持" |
| 竞争性偏向分数（面孔对/面孔阵列） | **不能** | 我们是**单张面孔**，屏幕上没有竞争刺激。我们的对照是**试次间**（悲伤试次 vs 高兴试次），不是试次内区域竞争。这是与多数元分析研究的实质性设计差异，必须在报告里写明，不得把两者当作同一个量 |
| 眼/嘴 AOI（dlib 68 点） | **能** | 改用项目已有的 YuNet（`Face Rules` 规定的检测器），在 36 张刺激图上离线求人脸框与 5 点关键点，构造 eyes / mouth / face-other / off-face 四个 AOI。AOI 只依赖刺激图，与被试无关，不存在泄漏 |
| scanpath 长度缩短 | **能** | 自由观看逐试次可算 |
| 反扫视错误率、潜伏期 | **能，但预期被年龄吸收** | 需从刺激视频解码靶位置时间序列 |
| 平滑追随增益、RMSE、追赶扫视 | **部分能** | 需从 `平滑追随.mp4` 解码靶轨迹。**峰速类特征在 60 Hz 的 Tobii 上不可靠**，见下 |
| 瞳孔基线校正的效价反应 | **能** | 两套设备都有 mm 瞳孔；用每试次前 1 s 中央十字作基线 |
| 排除数据丢失 ≥50% 的被试 | **能** | `validRatio`（七鑫易维）/ `Validity left/right` 占比（Tobii） |
| 嵌套被试级 CV | **已经是项目默认** | 沿用固定 split，不重新划分 |
| 与人口学基线比较增量 | **已经是项目默认，且比文献严格** | 我们额外要求比较者本身高于随机，并对 <500 人队列做置换检验 |

### 采样率决定了哪些特征能算

这是本模态特有的、文献里几乎没人处理的问题：

| 特征族 | Tobii 60 Hz | qixin 120 Hz | qixin 500 Hz |
|---|---|---|---|
| dwell / 注视次数 / 注视时长 / AOI 占比 | 可 | 可 | 可 |
| 瞳孔均值、基线校正瞳孔反应 | 可 | 可 | 可 |
| 扫视潜伏期（±1 采样点） | ±16.7 ms，粗 | ±8.3 ms | ±2 ms |
| 扫视峰速、加速度 | **不可** | 勉强 | 可 |
| 平滑追随速度增益 | 低置信 | 可 | 可 |

因此特征集必须分层：**`core`（三设备都能算，可跨设备比较）** 与
**`extended`（仅 120/500 Hz）**。绝不把 60 Hz 估出的峰速和 500 Hz 的放进同一列。

---

## 四、建议的方法

### 4.1 总原则

Goal 2.10 与 Goal 2.9 一样，**只替换特征层**：同一批固定 split、同一套内层 CV、
同样的模型族与网格、同样的 1000 次自助与配对检验、同样排除 pilot holdout。
不引入深度模型，不做多模态融合，不解 Goal 3/4/5 的闸。

### 4.2 分析单元

`device × task` 为一个 unit，共 9 个，外加每设备一个三任务交集队列，共 12 个：

| unit | 预计 CV 人数 |
|---|---|
| tobii × {free_viewing, saccade, smooth_pursuit} | 252 / 253 / 253 |
| qixin_120 × {free_viewing, saccade, smooth_pursuit} | 324 / 323 / 336 |
| qixin_500 × {free_viewing, saccade, smooth_pursuit} | 306 / 320 / 328 |
| 每设备三任务交集 | 待测，约 250–320 |

**全部 12 个 unit 都在 500 人以下**，所以按 `EXPERIMENT_PROTOCOL.md`，
**任何被credit的增量都必须先过标签置换检验**。这一点在开工前就已经确定。

### 4.3 特征集设计

**A. `free_viewing`（主分析）**

按效价 v ∈ {happy, sad, neutral} 与窗口 w ∈ {early 0–1 s, late 1–4 s} 聚合，AOI ∈ {eyes, mouth, face_other, off_face}：

- 维持性注意：各 (v, w, AOI) 的 dwell 占比、注视次数、平均注视时长；
- 全局：每试次 scanpath 长度、注视分散度（BCEA）、首次注视潜伏期与首次注视 AOI；
- 效价对照（显式构造，与绝对量并列提交）：
  `sad − neutral`、`happy − neutral`、`sad − happy`，对 dwell / 注视次数 / 平均注视时长各一组；
- 瞳孔：以试次前 1 s 中央十字为基线的 mm 变化，按 (v, w) 聚合，以及 `sad − neutral`、`happy − neutral`；
- 稳定性：36 试次上按效价的被试内标准差。

**B. `saccade`**

从 `前扫视-正式.mp4` / `反扫视-正式.mp4` 逐帧解码靶位置，得到靶跳时刻与方向：
- 前扫视：潜伏期分布（中位、IQR、偏度）、正确方向率、增益；
- 反扫视：**方向性错误率**、纠正率、纠正潜伏期、正确试次潜伏期；
- 对照：`anti − pro` 潜伏期差（抑制代价）——这是被试内量，抵消个体基础速度；
- 仅 120/500 Hz：峰速、峰速-幅度主序列斜率。

**C. `smooth_pursuit`**

从 `平滑追随.mp4` 解码靶轨迹：
- 速度增益（水平/垂直/沿靶方向）、位置 RMSE、追赶扫视率（±45°、≥1.5°）、
  反向扫视率、追随中断时长占比；
- 60 Hz 设备上速度类特征标注 `timing_confidence: low`，只进 sensitivity 分析
  （与 fNIRS 的 Bikom VFT 同一处理方式）。

**D. `qc`（独立特征集，参与 `signal_qc vs qc` 对照）**

`validRatio`、有效采样占比、标定精度与精密度（Tobii 有 18 列）、
眨眼率、丢失段数与最长丢失段、录制时长与范式期望时长之差、录制次数（是否重录）。

### 4.4 必须做的对照

沿用项目既有的对照结构，逐条报告：

- `demographics`（age+sex+grade，纯净，不含 site proxy）
- `demographics_group` / `group_proxy_only`（site proxy，单独列，**绝不并入 demographics**）
- `qc` / `qc_demographics`
- `signal` / `signal_demographics` / `signal_qc_demographics`
- **增量只在 `signal_demographics vs demographics` 上计分**；赢 background / qc 只是捷径对照。

### 4.5 本模态特有的额外验证

1. **无标签效度验证（先于任何建模）**。三个设备各自独立地检查：
   - 自由观看：眼区注视占比应显著高于嘴区（人脸浏览的普遍规律）；
   - 反扫视错误率应显著高于前扫视错误率；
   - 平滑追随增益应落在 0.7–1.0 的生理范围；
   - 瞳孔应对刺激起始出现可见的光反射/定向反应。
   任一设备通不过，说明是解析问题而不是数据问题——这正是 Goal 2.7 在 EEG/fNIRS 上栽过的跟头。

2. **分半信度**。对每个特征，用奇数试次 vs 偶数试次算 Spearman-Brown 校正的分半相关，
   写进特征表。信度 < 0.5 的特征在报告里标注，但**不预先剔除**（剔除会构成选择偏倚）。

3. **跨设备一致性**。同一个特征在三个设备上的分布与其和年龄的相关方向应当一致。
   不一致就是解析或量纲问题。两个双设备被试太少，不足以做被试内验证，只能做分布级比较。

4. **年龄吸收的显式量化**。对反扫视错误率等发育敏感指标，报告
   `Spearman(feature, age)`，并报告"回归掉年龄之后还剩多少单变量 AUROC"。
   这不是模型选择，是解释性证据。

### 4.6 事先写下的预测

在跑任何模型之前记录，跑完后对照，避免事后解释：

1. 自由观看的效价对照会有**微弱但方向正确**的单变量信号（`sad − neutral` dwell 的
   AUROC 约 0.52–0.56），量级低于文献报告的 SMD 0.59–0.71 所对应的水平。理由：
   我们是青少年筛查队列（33% 阳性，非临床 MDD）、4 s 而非 8–10 s、单面孔而非竞争呈现。
2. 反扫视错误率会有中等单变量信号，但**在 demographics 增量上归零**，因为它和年龄强共线。
3. QC 特征（`validRatio`、标定精度）会有非平凡的单变量信号，且部分与采集点共线。
   这是捷径不是信号，`signal_qc vs qc` 对照必须能把它揭出来。
4. 综合判断：**12 个 unit 中被credit的增量，最可能是 0 个**。
   眼动是第五个特征层；前四层（EEG、fNIRS、面部、行为学）都是零增量。
   眼动的先验优于它们（被试内效价对照、文献效应量更明确），但队列规模小一个量级
   （919 vs 3597），而 <500 人正是 Goal 2.9 制造出假阳性的那个区间。

如果结果确实是零，本阶段的价值在于：这是**第一个被试内对照设计**的零结果，
比"整段录制的统计量没有信号"信息量高得多。

### 4.7 实施顺序

1. `scripts/audit_eye_readiness.py` → `reports/eye_readiness_audit.md`：
   覆盖、去重、范式一致性、QC 分布、无标签效度验证。
2. `configs/goal2_10/paradigm_spec.yaml`：眼动范式规格。
   注意 `附件/` 无眼动范式脚本，每个值的 `source:` 必须写明是
   `stimulus_media` 还是 `recorded_timeline`，并标注这是**数据推导而非附件推导**。
3. 刺激侧离线产物：36 张人脸的 YuNet AOI、两段扫视视频的靶位置序列、
   平滑追随靶轨迹。这些与被试无关，只做一次。
4. `scripts/extract_eye_goal2_10_features.py`。
5. `scripts/run_goal2_10.py`（复用 `goal2_9` 的 runner）。
6. `scripts/summarize_goal2_10.py` + 报告。

---

## 参考文献

- Emotional stimulation processing characteristics in depression: Meta-analysis of eye tracking findings. <https://pmc.ncbi.nlm.nih.gov/articles/PMC9880408/>
- Attentional biases to emotional information in clinical depression: A systematic and meta-analytic review of eye tracking findings. <https://pubmed.ncbi.nlm.nih.gov/32663997/>
- Eye Movement Abnormalities in Major Depressive Disorder. <https://pmc.ncbi.nlm.nih.gov/articles/PMC8382962/>
- Eye movement characteristics of emotional face recognizing task in patients with mild to moderate depression (CFAPS, dlib 68 点 AOI). <https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2024.1482849/full>
- Deep learning characterizes depression and suicidal ideation in young adults from eye movements. npj Digital Medicine. <https://www.nature.com/articles/s41746-026-02550-4>
- Identifying depression with mixed features: the potential value of eye-tracking features. <https://pmc.ncbi.nlm.nih.gov/articles/PMC11961420/>
- The reliability of attentional biases for emotional images measured using a free-viewing eye-tracking paradigm. <https://link.springer.com/article/10.3758/s13428-018-1147-z>
- The reliability of eyetracking to assess attentional bias to threatening words in healthy individuals. <https://link.springer.com/article/10.3758/s13428-017-0946-y>
- Normative Values for Prosaccade and Antisaccade Eye Movements in Adolescents. <https://pubmed.ncbi.nlm.nih.gov/42403969/>
- Inhibiting saccades to a social stimulus: a developmental study. <https://www.nature.com/articles/s41598-020-61188-8>
- Metrics of two-dimensional smooth pursuit are diverse across participants and stable across days. <https://pmc.ncbi.nlm.nih.gov/articles/PMC11801394/>
- The fundamentals of eye tracking, Part 7: Determining data quality. <https://link.springer.com/article/10.3758/s13428-026-03039-4>
- Eye-tracking data quality as affected by ethnicity and experimental design. <https://link.springer.com/article/10.3758/s13428-013-0343-0>
- Assessing hypo-arousal during reward anticipation with pupillometry in patients with major depressive disorder. <https://www.nature.com/articles/s41598-023-48792-0>
- Diagnosing and tracking depression based on eye movement in response to virtual reality（7invensun 设备）. <https://pmc.ncbi.nlm.nih.gov/articles/PMC10875075/>
- AI-Based Screening for Depression and Social Anxiety Through Eye Tracking（**反例**：图像级划分、被试级泄漏）. <https://arxiv.org/abs/2503.17625>

---

## 审计回填（2026-09-08，第 1 步完成后）

本节记录就绪审计对上文的修正。上文不作删改。

**1. 扫视任务的试次数比预期少得多。** §4.3-B 假设反扫视有足够试次支撑错误率。
实际每个正式 block 只有 **8 个试次**（首次 1500 ms、周期 2500 ms、靶亮 1000 ms，
左右各 4、大小幅度各 4）。错误率分辨率 0.125，与文献 40–100 试次的组套不可比。
§4.6 的预测 2（"反扫视有中等单变量信号但被年龄吸收"）因此进一步弱化：
它可能连中等单变量信号都达不到，纯粹因为测量精度不足。必须与分半信度一起报告。

**2. 新增一处必须处理的时钟缺陷。** §3 的表格没有预见到采样时钟问题。
七鑫易维 F500 的采样跨度比工程文件记录的 `duration` 长约 0.4%，
到 136 s 追随段末累积成 300–400 ms 偏移；未校正时追随相关只有 0.64–0.72，
按 `duration` 重标定后为 0.935 [0.913, 0.953]。所有七鑫易维轨迹在任何试次锁定使用前
必须经 `chongqing_binary.eye.qixin.aligned_time_ms` 映射。Tobii 另有微秒/毫秒单位差异。

**3. 覆盖数好于预期。** §1.1 估计 CV 内 919 人，审计确认 919 人、1187 名唯一被试、
3481 条有效记录，且 9 个 unit 全部通过无标签效度检查。§4.2 的"12 个 unit"应改为
**9 个 `device × task` unit 加 3 个每设备三任务交集队列**；交集队列规模待第 4 步测定。

**4. Tobii 的采集质量明显低于两台七鑫易维**（有效采样 0.897 vs 0.975–0.980，
长丢失段中位 5 vs 1，9 条记录有效率低于 0.5）。由于设备与采集点共线，
这是一个捷径候选，§4.4 的 `signal_qc vs qc` 对照必须能把它揭出来。

**5. §4.5 的"无标签效度验证"已执行且全部通过**，结果见审计报告。
其中"眼区注视占比应高于嘴区"一项尚未执行，因为它需要 YuNet 子 AOI，
属于第 3 步；本次执行的是更基础的"注视落在刺激人脸框内"，
三设备均为随机水平的 18 倍以上。

---

## 审计回填（2026-09-09，第 2/3 步完成后）

**6. 必须新增一道注视漂移校正，否则眼/嘴 AOI 是站点捷径而不是行为。**
§4.3-A 直接把眼/嘴 AOI 占比当作可用特征，这是错的。三台设备报告的注视点
都系统性低于真实注视位置，幅度依设备而异（以范式自带的中央十字量得：
Tobii +0.015 屏高、qixin_120 +0.056、qixin_500 +0.052）。
眼带与嘴带各约 0.10 屏高，该偏移足以让"眼区 > 嘴区"这条铁律在两台七鑫易维上反转
（eyes−mouth 原始值 −0.103 / −0.145，Tobii 为 +0.245）。
由于设备与采集点共线，未校正的 0.04 差异会以"行为发现"的外衣进入模型，
实际是站点捷径。

校正方法：取每条记录全部十字（36–37 个）的注视中位数减屏幕中心，
跳过每个十字前 200 ms。校正后 eyes−mouth 为 +0.362 / +0.339 / +0.269，
设备间极差从 0.390 降到 0.093。偏移量本身进 **QC 特征集**，不进信号特征集。

**7. 第 1 步的粗检查放过了这个问题，这一点本身要记住。**
"注视落在人脸框内"在三设备都是随机水平的 18 倍，看起来完美——
但人脸框关于屏幕中心上下对称（y 0.335–0.665），垂直平移照样落在框内。
**粗粒度效度检查通过，不构成坐标系正确的证据。** 只有比人脸更细的分区才能发现。

**8. 残余设备差异仍在**（校正后眼区占比 0.481–0.539）。相对原始差异很小但不为零，
所以 §4.1 的"分设备建模、禁止跨设备合并原始特征"继续有效，不因校正而放宽。
