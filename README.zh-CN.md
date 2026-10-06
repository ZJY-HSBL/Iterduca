# Iterduca

**现代桌面网络路由客户端**

Iterduca 是一款 Windows 优先的桌面代理与网络路由客户端，使用 Python + PyQt6 开发，以 Mihomo 作为外部路由核心。项目将桌面界面、配置管理、运行时配置、系统网络集成和核心进程生命周期明确分层，而不是把所有逻辑直接堆在 UI 事件中。

> 当前版本：**v0.2.0**

[English README](README.md)

## 项目定位

Iterduca 不是其他桌面客户端的换皮或 Fork。桌面应用层独立实现，并通过明确的 Core Adapter 与代理核心交互。目前首个适配核心为 Mihomo，但 UI、配置模型与核心进程彼此解耦，为后续扩展保留清晰边界。

**Iterduca** 的命名取自“引导旅程”的拉丁语意象：让每一次连接沿合适的路径抵达目标。

## v0.2.0 已实现

- PyQt6 桌面客户端与深色界面
- YAML 配置导入与本地管理
- 原始 Profile 保持不变，运行时单独生成配置
- Mihomo Core 启动、停止与日志读取
- 本地 Controller API 与随机 Secret
- Rule / Global / Direct 模式实时切换
- 代理组读取与节点切换\n- 单节点延迟测试\n- Connections 实时连接查看、单连接关闭与全部关闭\n- Rules 规则表格与客户端过滤\n- 订阅 URL 导入与原位更新
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

TUN 没有被粗暴地塞入首个 MVP。它涉及管理员权限、系统路由、DNS、异常恢复等独立问题，应当在普通系统代理稳定后单独设计和测试。

## 安全设计

Iterduca 默认只允许本机访问 Mihomo Controller，并使用随机 Bearer Secret。导入的 Profile 作为源配置保留，不会被运行时逻辑覆盖。Iterduca 当前也不存在用于上传 Profile、订阅内容、流量或日志的云服务。

Profile 中可能包含代理服务器认证信息，请勿把个人配置提交到公开 Git 仓库。

## License

Iterduca 使用 MIT License。Mihomo 是独立项目，遵循其自身许可证。
