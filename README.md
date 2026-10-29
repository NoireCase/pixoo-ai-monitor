# Pixoo AI Monitor

把 **Divoom Pixoo 第一代 16×16 像素屏**变成桌面 AI 额度显示器，自动轮播 OpenCode Go、Codex 和 DeepSeek 的真实数据。

第一次使用，请按「环境准备 → 首次安装 → 日常操作」顺序完成，无需修改 Python 源码。

## 1. 环境准备

| 需要什么 | 说明 |
| --- | --- |
| 设备 | 原版 Pixoo 16×16，USB 供电；不适用于 Pixoo 64 / Max / Wi-Fi HTTP API |
| 电脑 | Windows 10/11 x64，蓝牙开启，适配器支持 Bluetooth Classic / RFCOMM |
| Python | Python 3.10+，推荐 3.11 或 3.12；从 [Python 官网](https://www.python.org/downloads/windows/)安装，保留 Tcl/Tk、Python Launcher，并勾选添加到 PATH |
| 网络 | 首次下载依赖、刷新真实额度时需要联网 |
| 平台账户 | 按需要配置自己的 OpenCode Go Key、DeepSeek 官方 API Key；仅使用部分平台也可以 |
| Codex（可选） | 需要读取 Codex 额度时，先按 [官方 CLI 文档](https://developers.openai.com/codex/cli/)安装并登录 CLI |

**下载：[v0.2.0 健康自检与画面图解版本](https://github.com/NoireCase/pixoo-ai-monitor/releases/tag/v0.2.0)**。下载 `pixoo-ai-monitor-v0.2.0-windows-source.zip`，右键「全部解压缩」，进入解压后的项目文件夹。不要在 ZIP 内直接双击脚本。

这是需要 Python 的源码发行包，不是免安装 EXE。Git、Docker、Electron 均不是运行前提。

## 2. 首次安装：从下载到亮屏

### 第一步：安装依赖

进入解压后的项目文件夹，在资源管理器地址栏输入 `powershell` 并回车，在该窗口执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

脚本会创建 `.venv`、下载依赖，并在不存在时生成 `config.json`。第一次安装需要等下载完成；看到 `Setup complete` 再继续。此命令仅对本次脚本进程设置执行策略，不修改系统的全局执行策略。

### 第二步：配对 Pixoo

1. 给 Pixoo 通电，靠近电脑。
2. 打开 Windows「设置 → 蓝牙和设备（或设备）→ 添加蓝牙设备」，配对 Pixoo。
3. 关闭或断开手机 Divoom App 对 Pixoo 的连接。
4. 再运行一次第一步命令，让程序尝试发现设备。自动发现只识别注册表中的候选设备，不代表已经通信成功。
5. 用记事本打开 `config.json`。如果 `mac` 为空或发现了多个设备，请填写自己的设备 MAC；`port` 默认是 RFCOMM channel 1。先保留其他参数。

### 第三步：配置你要看的服务

双击 `set-key.bat`，输入平台代号并回车：

| 输入 | 粘贴的密钥 |
| --- | --- |
| `go` | OpenCode Go 的 API Key |
| `ds` | DeepSeek 官方 API Key |

粘贴完整密钥并回车，核对可见内容后输入 `y` 保存。每次只保存一个服务；要设置另一个，再运行一次。密钥保存到当前 Windows 用户的 Credential Manager，不能填写到 `config.json`。

Codex 使用本机 CLI 的现有登录。在终端用 `codex login status` 检查；尚未登录时运行 `codex login` 并自行完成登录。不要向本项目粘贴 Codex 登录令牌。

**只有部分服务也能用。** 在 `config.json` 中将 `enabled` 改为需要的平台，例如仅 Codex：

```json
"enabled": ["cx"]
```

`go` = OpenCode Go，`cx` = Codex，`ds` = DeepSeek。保留在列表中但未配置的服务会显示 `SET`，不会让其他服务停止。

### 第四步：确认硬件亮屏

确保监控未运行，再双击 `hardware-test.bat`。你应依次看到红、绿、蓝和 GO 72 测试图。这里的 GO 72 是硬件测试数据，不是账户额度。

**必须亲眼看到测试画面才算成功。** 只有“已配对”或“扫描到设备”不等于能够发送图像。失败时先运行 `diagnose.bat`，并查看下方排错说明。

### 第五步：启动真实轮播

双击 `start.bat`，保持程序运行。默认每 5 秒切换页面，每 120 秒刷新各服务的数据。若系统出现重复实例提示，说明已有监控运行，无需再启动。

## 3. 日常操作

| 想做什么 | 操作 |
| --- | --- |
| 启动真实额度轮播 | 双击 `start.bat` |
| 正常停止 | 双击 `stop.bat`，等当前操作结束后退出 |
| 预览模拟画面 | 双击 `preview.bat`；窗口标明 MOCK，不能当作真实额度 |
| 更新密钥 | 重新运行 `set-key.bat`，然后重启监控或等下次刷新 |
| 检查设备/环境 | 双击 `diagnose.bat` |
| 检查监控是否健康 | 双击 `health-check.bat`，只读检查进程、心跳、蓝牙发送及各平台刷新 |
| 登录后自动启动 | 主动执行一次 `autostart.bat`，不随普通安装自动启用 |
| 关闭登录自启 | PowerShell 执行 `Unregister-ScheduledTask -TaskName "Pixoo AI Monitor"` |

改亮度、轮播间隔或样式时，用记事本编辑 `config.json`，保存后先运行 `stop.bat`，等待退出，再运行 `start.bat`。常用项：

| 配置项 | 默认值 / 含义 |
| --- | --- |
| `brightness` | `50`，亮度范围 0～100 |
| `rotation_seconds` | `5`，页面停留秒数 |
| `refresh_seconds` | `120`，API 刷新间隔秒数 |
| `display_style` | `"b3"`；也支持 `"b2"`、`"classic"` |
| `windows` | `["5H", "7D", "30D"]`；B3 虽显示 W，配置仍用 `7D` |
| `enabled` | `["go", "cx", "ds"]`，需要展示的平台 |

JSON 要保留双引号、逗号和括号。详细参数见 [使用说明.txt](使用说明.txt)。

### 旧版本升级

先运行旧目录的 `stop.bat` 并等待退出。备份自己的 `config.json`，解压新版到新目录，将个人配置复制到新目录；不要把旧 `.venv` 直接搬过去。按安装步骤重新运行 `setup.ps1`，再运行 `start.bat`。同一 Windows 用户的 Credential Manager 凭据保留，不随解压覆盖。启用了登录自启时，在新目录重新执行 `autostart.bat` 以更新任务路径。

`health-check.bat` 的结论为 HEALTHY（健康）、DEGRADED（运行中有异常）、UNHEALTHY（未运行或不健康）或 UNKNOWN（信息不足）。旧进程没有心跳时需要正常重启一次。自检不读密钥、不请求额度接口、不另开蓝牙、不自动重启；传输成功也不等于设备画面已经被人看到。

## 4. B3 屏幕怎么看

左上角 O / G / D 分别代表 OpenCode Go / Codex / DeepSeek；右上角 H / W / M / ¥ 分别代表 5 小时 / 7 天 / 30 天 / 人民币。

- 中间白字：OpenCode Go、Codex 显示剩余额度百分比；100 不带百分号，其余额度带百分号。DeepSeek 显示真实余额，按像素空间处理小数或缩写。
- H 页倒数第二行：固定五格重置倒计时，每格一小时。完整小时绿色，最后不足一小时且超过 30 分钟绿色，不超过 30 分钟红色；空格暗灰。
- 额度页最后一行：固定 14 格，从左填充；剩余 ≥60% 绿、≥20% 黄、<20% 红。空格暗灰。
- DeepSeek 最后一行：API 高峰时段红条、空闲时段蓝条、未知灰条，与余额多少无关。
- `SET` = 未配置；`ERR` = 请求失败；`OLD` = 旧数据或过期。不要把异常页面当成实时余额。

下面的图片均由**生产 B3 Renderer 和明确的演示数据**生成：屏幕本体严格为 16×16 RGB，最近邻放大，文字说明位于屏幕外。它们展示程序实际会画出的像素，**不是实机照片，也不是维护者的真实额度或余额**；LED 亮度和拍摄观感会因设备而异。

### 4.1 六个页面与平台标识

![B3 六页演示画面，全部为合成数据](docs/screens/pages.png)

从左到右、从上到下依次为 O/H、O/W、O/M、G/H、G/W、D/¥。周额度使用 W；100 不显示百分号，其余额度带小百分号。DeepSeek 仅显示人民币余额，不添加百分号。

### 4.2 剩余额度：绿色、黄色、红色

![100、60、59、20、19、0 百分比的演示画面](docs/screens/quota-states.png)

| 演示剩余量 | 额度条表现 |
| --- | --- |
| 100%、60% | 绿色，从固定轨道左端填充 |
| 59%、20% | 黄色，未填充部分为暗灰 |
| 19% | 红色，数字仍为白色 |
| 0% | 轨道全暗灰，不保留虚构的红色长度 |

以上图片采用 W 页，以便单独观察最后一行额度条。

### 4.3 H 页重置倒计时

![五格倒计时的不同边界和缺失时间演示](docs/screens/countdown-states.png)

五格轨道始终位于同一位置，不会因为剩余时间减少而移动。3h25m 为「绿、绿、绿、红、灰」，3h35m 和 4h 整均为「绿、绿、绿、绿、灰」。30m 为第一格红色；0m 或重置时间不可用时全灰。图中 `No reset time` 是缺失时间的演示，不代表额度为零。

### 4.4 异常：SET、ERR、OLD

![未配置、读取失败、旧数据的演示画面](docs/screens/error-states.png)

| 屏幕文字 | 含义 | 建议操作 |
| --- | --- | --- |
| SET | 未配置对应密钥或 Codex 登录 | 配置所需平台，或从 enabled 中移除不用的平台 |
| ERR | 接口请求失败且没有可用成功数据 | 检查网络、凭据和接口诊断 |
| OLD | 上次数据已过期或刷新失败后保留旧数据 | 等下次刷新，必要时运行健康自检 |

**OLD 是提示文字，不是余额“0D”。** v0.2.0 已补齐 L 字形，三个字母会完整显示；单个平台异常不会把其他平台的正常页面隐藏。

### 4.5 DeepSeek：价格高峰、空闲、未知

![DeepSeek 高峰红条、空闲蓝条、未知灰条的演示画面](docs/screens/deepseek-states.png)

三张图使用**相同的演示余额**，底栏仅随价格时段改变：高峰红、空闲蓝、规则或日历不确定时灰。它不是余额百分比，也不依赖 B2 的参考峰值。

每个示例另有原始 `_16.png` 和最近邻放大的 `_320.png`，见 [屏幕素材目录](docs/screens)。开发者可用 `python scripts/generate_readme_previews.py` 离线重新生成，不需要密钥或设备。

## 5. 注意事项与常见问题

**三个来源互不混用。** OpenCode Go 套餐额度、Codex 订阅限额、DeepSeek 官方余额是三套数据；Codex 页面不是普通 ChatGPT 聊天次数，也不是 OpenAI API 余额。OpenCode 非官方额度接口可能变化。

**连接超时 / 没有画面：** 检查供电、蓝牙和手机占用；不要同时启动硬件测试和监控。使用 `diagnose.bat` 与 `monitor.log` 排查。端口 1 超时不一定说明端口错误，不要盲目扫端口。程序会自动重连，退避最长 60 秒。

**密钥与分享：** 设置密钥时窗口可见，使用后关闭窗口。环境变量 `PIXOO_GO_KEY` / `PIXOO_DS_KEY` 优先于 Credential Manager。真实导出图包含用量或余额，不要连同 `config.json`、日志、备份、登录文件一起分享。仓库与发行包只提供空的示例配置。

**倒计时全灰：** 可能是重置时间缺失、已经过去、数据过期或系统时钟变化。开启 Windows 时间同步；可运行 `.\.venv\Scripts\python.exe b3_diagnose.py` 查看原因。倒计时在本地更新，不会因此每分钟请求 API。

**DeepSeek 灰条：** 离线日历当前仅覆盖已确认的 **2026 年法定日期**。未覆盖年份显示 UNKNOWN，需核实官方信息后更新 `data/china_statutory_holidays.json` 并重启。普通调休休息日不直接当作法定节日；调休周末仍按周末空闲。价格规则可独立维护于 `data/deepseek_price_rules.json`。

**已知验证范围：** 在一台 Windows 电脑和原版 Pixoo 上完成真实六页显示与目视确认；本版150项自动化测试通过，覆盖健康自检、渲染和文档图像一致性。尚未全面验证不同蓝牙驱动、长期运行及真实睡眠唤醒后的恢复。其他设备仍需自行完成硬件测试。

## 6. 技术简介（开发者可选读）

Python + Pillow + 原生像素字体；Tkinter 模拟器与设备复用渲染代码；Classic RFCOMM 发送图像。三个 Provider 独立刷新，API 请求与画面轮播解耦；使用轮转日志和单实例保护。

```powershell
# 在项目目录、完成 setup 后运行
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe export_visual_review.py --style b3
.\.venv\Scripts\python.exe preview_b3_samples.py
.\.venv\Scripts\python.exe health_check.py --json
```

真实导出是重新读取额度的独立快照，不截取后台缓存，也不占用蓝牙。`test-samples` 下的 TEST 图片为合成测试数据。

健康自检使用原子更新的 `runtime-status.json`。判断包括 PID 创建时间、可识别重复实例、主循环心跳、Provider 刷新停滞和数据过期；相同画面跳过发送不会被误判为卡死。读取权限不足时输出 UNKNOWN。退出码为 0 健康、1 有异常、2 未运行或不健康、3 信息不足。心跳文件属于本机运行数据，不应提交。

问题反馈请描述 Windows / Python 版本、Pixoo 型号和可复现步骤，并先脱敏日志；不要提交密钥、令牌、设备地址或真实余额截图。提交改动前请运行完整测试，保留 classic / b2 的兼容性。

## 7. 许可证与致谢

本项目采用 [MIT License](LICENSE)，Copyright (c) 2026 NoireCase。
蓝牙驱动基于 [PixooCtrl](https://github.com/ferzkopp/PixooCtrl) 改写，原作者 Andreas Schiffler 的 MIT 许可单独保留在 [LICENSE-PixooCtrl](LICENSE-PixooCtrl)。完整来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

版本变更见 [CHANGELOG.md](CHANGELOG.md)。
