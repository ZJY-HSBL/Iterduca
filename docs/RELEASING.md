# Iterduca Release Process / 发布流程

Iterduca uses release branches as immutable release candidates.

从 v1.7.0 开始，Iterduca 使用 `release/vX.Y.Z` 分支作为正式发布触发器。

## Normal release / 正常发布

1. Finish the version changes on a development branch.
2. Ensure both **CI** and **Installer CI** pass.
3. Fast-forward `main` to the validated version commit.
4. Ensure the same commit passes CI on `main`.
5. Create `release/vX.Y.Z` from that exact commit.
6. GitHub Actions automatically derives tag `vX.Y.Z`, verifies it matches `pyproject.toml`, builds the Windows artifacts, creates the Git tag, and publishes the GitHub Release.

中文流程：

1. 在开发分支完成版本功能和版本号更新。
2. 确认 **CI** 与 **Installer CI** 全部通过。
3. 将 `main` 快进到已经验证的版本提交。
4. 再确认 `main` 上同一提交的 CI 通过。
5. 从该提交创建 `release/vX.Y.Z`。
6. GitHub Actions 自动解析 `vX.Y.Z`，校验其与 `pyproject.toml` 一致，构建 Windows 资产，创建 Git Tag，并发布真正的 GitHub Release。

## Release artifacts / 发布资产

A normal Windows release publishes:

- `Iterduca-vX.Y.Z-windows-x64.exe`
- `Iterduca-vX.Y.Z-windows-x64.zip`
- `Iterduca-vX.Y.Z-windows-x64-setup.exe`
- `SHA256SUMS.txt`

The Setup installer is also covered by GitHub Release Asset SHA-256 digest metadata. Iterduca's built-in application updater requires the Setup digest, `SHA256SUMS.txt`, and the downloaded file hash to agree before installation.

Setup 安装包同时具有 GitHub Release Asset 的 SHA-256 digest。Iterduca 内置更新器只有在 Asset digest、`SHA256SUMS.txt` 与实际下载文件三者哈希完全一致时才允许安装。

## Manual fallback / 手动备用

The **Release** workflow still supports `workflow_dispatch`. Use it only when the automatic release-branch trigger needs to be retried. The supplied tag must exactly match the project version.

**Release** 工作流仍保留手动 `workflow_dispatch`。仅在自动发布需要重试时使用，输入 Tag 必须与项目版本完全一致。

## Invariants / 发布约束

- Never create a release branch from an unvalidated commit.
- Never change files on an existing release branch.
- Never reuse a version number for different source code.
- Keep `main`, `release/vX.Y.Z`, the Git tag, and the GitHub Release on the same release commit.
- A failed build must not be promoted by creating a new tag manually.

- 不从未验证提交创建 Release 分支。
- 不在已经锁定的 Release 分支上继续改代码。
- 不使用同一个版本号发布不同源码。
- `main`、`release/vX.Y.Z`、Git Tag 与 GitHub Release 应对应同一个发布提交。
- 构建失败时不通过手工创建 Tag 绕过验证。
