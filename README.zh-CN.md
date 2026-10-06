# Iterduca

**现代桌面网络路由客户端**

Iterduca 是一款 Windows 优先的桌面代理与网络路由客户端，使用 Python + PyQt6 开发，以 Mihomo 作为外部路由核心。项目将桌面界面、配置管理、运行时配置、系统网络集成和核心进程生命周期明确分层，而不是把所有逻辑直接堆在 UI 事件中。

> 当前版本：**v0.9.0**

[English README](README.md)

## 项目定位

Iterduca 不是其他桌面客户端的换皮或 Fork。桌面应用层独立实现，并通过明确的 Core Adapter 与代理核心交互。目前首个适配核心为 Mihomo，但 UI、配置模型与核心进程彼此解耦，为后续扩展保留清晰边界。

**Iterduca** 的命名取自“引导旅程”的拉丁语意象：让每一次连接沿合适的路径抵达目标。

## v0.9.0 已实现

- PyQt6 桌面客户端与深色界面
- YAML 配置导入与本地管理
- 原始 Profile 保持不变，运行时单独生成配置
- Mihomo Core 启动、停止与日志读取
- 本地 Controller API 与随机 Secret
- Rule / Global / Direct 模式实时切换
- 代理组读取与节点切换\n- 单节点延迟测试与当前代理组批量测速\n- Connections 实时连接查看、单连接关闭与全部关闭\n- Rules 规则表格与客户端过滤\n- 订阅 URL 导入、原位更新与一键更新全部订阅\n- Runtime YAML 覆写编辑器与嵌套 deep-merge\n- Connections 页面可见时自动刷新
- Windows TUN 管理页面、管理员权限状态与 UAC 提权重启
- 支持 mips / system / gvisor / mixed 四种 TUN 协议栈
- TUN Auto Route、出口网卡自动检测、DNS Hijack 与 Strict Route 控制
- 可选绕过私网与链路本地网段，保留局域网访问
- 每次启动 Core 前执行 Mihomo `-t` 完整配置预检
- TUN 安全降级：停止 Core、关闭 TUN、回到普通代理模式
- TUN 运行时不会额外叠加 Windows WinINet 系统代理
- 单实例运行与本地 IPC 唤醒，避免重复启动多个 Core
- Windows 开机启动，支持后台直接驻留系统托盘
- 自动从应用目录、当前目录和 PATH 查找 Mihomo Core
- Settings 中一键检测 Mihomo 版本
- Windows 打包 EXE 写入正式文件版本信息
- Release 同时生成独立 EXE、Portable ZIP 与 SHA256SUMS
- Rule Providers 页面，支持刷新、单个更新和批量更新
- Overview 实时显示 Mihomo Core 内存占用
- Profile 安全删除；删除活动配置时先停止 Core
- 删除 Profile 时同步清理对应订阅元数据
- 订阅请求 User-Agent 自动跟随 Iterduca 当前版本
- Proxy Providers 页面，支持刷新、单个更新、批量更新和健康检查
- Provider 表格显示节点总数与当前可用节点数
- Tools 页面支持清理 DNS Cache 与 Fake-IP Cache
- Rules 表格显示规则索引、启用/禁用状态和命中次数
- 支持当前 Mihomo 会话内临时启用/禁用单条规则
- DNS Query 支持 A / AAAA / CNAME / MX / TXT 查询
- Tools 中以结构化格式展示 DNS 返回结果
- 应用与 Core 日志持久化保存并自动轮转
- 程序重启后 Logs 页面恢复最近持久日志
- 支持日志导出与清空持久日志
- Connections 可查看选中连接的完整 Controller 原始详情
- Rules 可查看选中规则的完整 Controller 原始详情
- 基于 GitHub Releases 的只读更新检查与语义版本比较
- 基于 Controller WebSocket 的实时上传/下载速率
- Mihomo 标准输出日志查看
- Windows WinINet 系统代理开启与恢复
- 系统托盘：显示、启动、停止、退出
- 本地设置持久化
- Runtime Config、Profile、Settings、Core Command 单元测试
- Windows GitHub Actions CI

## 软件架构

```text
┌────────────────────────────────────┐
│            PyQt6 Desktop           │
│ Overview · Proxies · Profiles      │
│ Logs · Settings · System Tray      │
└─────────────────┬──────────────────┘
                  │
               服务层
                  │
      ┌───────────┴───────────┐
      │                       │
配置 / 设置服务          Mihomo Adapter
      │                 REST + WebSocket
      │                       │
运行时配置              Core 生命周期
      │                       │
      └───────────┬───────────┘
                  │
             Mihomo Core
```

导入的订阅或 YAML 文件不会被 Iterduca 直接修改。程序会从源配置生成独立的 `runtime/config.yaml`，仅覆盖 Iterduca 自己负责的 `mixed-port`、`external-controller`、`secret` 和路由模式等运行参数。

## 环境要求

- Windows 10 / 11
- Python 3.12+
- Mihomo 可执行文件

本仓库**不直接捆绑 Mihomo 二进制文件**。请从 MetaCubeX/mihomo 官方项目获取核心，然后在 Iterduca 的 **Settings** 页面选择其可执行文件。

Mihomo 官方项目：https://github.com/MetaCubeX/mihomo

## 源码运行

```powershell
git clone https://github.com/ZJY-HSBL/Iterduca.git
cd Iterduca
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m iterduca
```

也可以执行：

```powershell
.\scripts\run.ps1
```

## 首次使用

1. 打开 **Settings**，选择 Mihomo 可执行文件。
2. 根据需要修改 Mixed Port 和 Controller Port。
3. 打开 **Profiles**，导入有效的 Mihomo / Clash 兼容 YAML 配置。
4. 选中配置并点击 **Use selected**。
5. 回到 **Overview**，点击 **Start core**。
6. 如果希望使用 Windows 系统代理的应用流量进入 Iterduca，可在 Settings 中开启 System Proxy。

v0.1.0 会强制将 Controller 绑定至 `127.0.0.1`，同时每次构建运行时配置都会生成新的随机 Secret。

## 项目结构

```text
Iterduca/
├── src/iterduca/
│   ├── core/          # Mihomo API、进程与运行时配置
│   ├── models/        # 应用数据模型
│   ├── services/      # Profile 与 Settings 服务
│   ├── system/        # Windows 系统集成
│   └── ui/            # PyQt6 主窗口、页面与主题
├── tests/
├── scripts/
└── .github/workflows/
```

## 测试

```powershell
python -m pytest
python -m ruff check src tests
```

## 后续规划

下一阶段计划增加 Connections 连接查看、Rules / Rule Provider 管理、订阅 URL 更新、节点延迟测试、Core 更新、配置覆写、TUN、流量历史以及 Windows 安装包与签名。

v0.4.0 已加入受控 TUN 能力。Iterduca 会在 Windows 上检查管理员权限，默认使用 Mihomo 的 `mips` 协议栈，Strict Route 默认关闭，并在真正启动 Core 前先执行完整配置预检。

## 安全设计

Iterduca 默认只允许本机访问 Mihomo Controller，并使用随机 Bearer Secret。导入的 Profile 作为源配置保留，不会被运行时逻辑覆盖。Iterduca 当前也不存在用于上传 Profile、订阅内容、流量或日志的云服务。

Profile 中可能包含代理服务器认证信息，请勿把个人配置提交到公开 Git 仓库。

## License

Iterduca 使用 MIT License。Mihomo 是独立项目，遵循其自身许可证。
