# 本机恢复记录（2026-09-05）

- 项目：`/data/home/cqm/Project/Code/chongqing`，约 17 GB。
- 来源：`../chongqing_migration_20260827.tar.zst`；压缩包 SHA-256 与随附记录一致。
- Git 历史、原有未提交修改、实验缓存、预测、检查点及 200 张 Face contact sheets 已恢复。
- 原始数据已上传至：`/data/home/cqm/Project/Dataset/Chongqing`，并保持原数据根目录的内部结构。

## 进入项目

```bash
source /data/home/cqm/Project/Code/chongqing/activate.local.sh
```

此脚本配置原始数据路径、`PYTHONPATH`，并使用按 `migration/avmoe-requirements.lock.txt` 重建的 `avmoe` 环境（Python 3.9.25、PyTorch 1.13.0 + CUDA 11.7）。旧版 v1 EEG 工具使用 `source /data/home/cqm/Project/Code/chongqing/activate.v1.local.sh`，对应 `chongqing_v1`（Python 3.11.5、PyTorch 2.5.1 + CUDA 12.1，含 MNE）。外部大模型及下载缓存仍不在迁移包内。

## 验证与限制

- 文件清单中的 1355 个文件最终全部通过 SHA-256 校验，日志：`migration/local-files-verification-20260905.log`。
- `git fsck --full` 成功；存在两个 dangling blob，不影响仓库历史完整性。
- 7 个基线检查点在本机均存在，SHA-256 全部匹配历史清单。
- 配置本机数据路径后，两个专用环境均通过全部 109 个单元测试。
- 代码、配置、文档及已生成清单中的旧服务器绝对路径已统一更新为本机项目路径和数据路径。
- 空数据目录存在不代表原始数据就绪；依赖原始数据的任务须等待上传完成。
- 原项目阶段为 Goal 2.7 完成，下一步是 Goal 2.8，详见 `AGENTS.md` 与 `PROGRESS.md`。

解压后的首次 Git 状态检查和 Python 测试更新了 Git 索引及 7 个 `.pyc` 文件；这些文件随后从原压缩包恢复，并重新执行完整文件清单校验。后续正常开发再次更新这些运行时文件属于正常现象。
