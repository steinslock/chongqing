# 本机恢复记录（2026-09-05）

- 项目：`/data/home/cqm/Project/Code/chongqing`，约 17 GB。
- 来源：`../chongqing_migration_20260827.tar.zst`；压缩包 SHA-256 与随附记录一致。
- Git 历史、原有未提交修改、实验缓存、预测、检查点及 200 张 Face contact sheets 已恢复。
- 原始数据尚未上传，预定目录：`/data/home/cqm/Project/Dataset/Chongqing`。上传时应保持原数据根目录的内部结构，避免额外嵌套一层文件夹。

## 进入项目

```bash
source /data/home/cqm/Project/Code/chongqing/activate.local.sh
```

此脚本配置原始数据路径、`PYTHONPATH`，并使用现有 `M3DFEL` 环境（Python 3.9.25）。没有修改该共享环境的依赖。它不是原始 `avmoe` 环境的精确复刻；重新运行完整特征提取或 GPU 实验前，应按 `MIGRATION.md` 和 `migration/` 中的依赖快照恢复专用环境。外部大模型及下载缓存也不在迁移包内。

## 验证与限制

- 文件清单中的 1355 个文件最终全部通过 SHA-256 校验，日志：`migration/local-files-verification-20260905.log`。
- `git fsck --full` 成功；存在两个 dangling blob，不影响仓库历史完整性。
- 7 个基线检查点在本机均存在，SHA-256 全部匹配历史清单。
- 配置本机数据路径后，109 个单元测试中 108 个通过。
- 剩余 `test_manifest_checkpoints_exist` 直接检查历史清单中的 `/data4/qiangminc/code/chongqing/...` 绝对路径，因此在本机失败；历史清单和测试保留原样，实际文件已独立验证。
- 空数据目录存在不代表原始数据就绪；依赖原始数据的任务须等待上传完成。
- 原项目阶段为 Goal 2.7 完成，下一步是 Goal 2.8，详见 `AGENTS.md` 与 `PROGRESS.md`。

解压后的首次 Git 状态检查和 Python 测试更新了 Git 索引及 7 个 `.pyc` 文件；这些文件随后从原压缩包恢复，并重新执行完整文件清单校验。后续正常开发再次更新这些运行时文件属于正常现象。
