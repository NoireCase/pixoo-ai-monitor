# Pixoo AI Monitor

Windows 上的 Divoom Pixoo 第一代 16×16 Bluetooth Classic/RFCOMM 额度显示器。
支持 OpenCode Go 5H/7D/30D、Codex 订阅限额和 DeepSeek 官方 API 余额，三者独立。

## 安装

安装 Python 3.10+（推荐 3.11+），在项目目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

在 Windows 设置配对 Pixoo，并核对生成的 config.json。必要时填写自己的 MAC 和 RFCOMM channel；配对记录不等于通信已成功。先停止监控，再运行 hardware-test.bat 并目视确认测试图像。

运行 set-key.bat，分别保存 go、ds 的完整 API Key。输入会在窗口显示，核对后以 y 确认；密钥存入当前用户的 Windows Credential Manager。也支持 PIXOO_GO_KEY、PIXOO_DS_KEY 环境变量。Codex 使用本机已经登录的 CLI，不读取浏览器 Cookie。

## 运行

start.bat 启动；stop.bat 正常停止；修改配置后停止并重启。单实例保护避免争抢蓝牙。
preview.bat 使用明确标注的 MOCK 数据；diagnose.bat 检查环境。
autostart.bat 是可选的当前用户登录自启，必须主动执行。

## B3 显示

O/G/D 代表 OpenCode Go/Codex/DeepSeek，H/W/M/¥ 代表 5小时/7天/30天/人民币。主数字为剩余额度或余额，100不带百分号，其余额度带百分号。H页面 y=14 的固定五格代表重置倒计时；y=15 居中的14格代表剩余额度，60%以上绿、20%以上黄、否则红。

DeepSeek 底栏独立显示北京时间的 API 峰谷状态：高峰红、空闲蓝、未知灰，不按余额计算长度。规则位于 data/deepseek_price_rules.json；法定假日日历位于 data/china_statutory_holidays.json。当前仅缓存已确认的2026年法定日期，不包含补休；未覆盖年份 UNKNOWN。未来应核实官方数据后维护，更新后重启。

config.example.json 无设备标识和密钥。display_style 支持 classic、b2、b3；默认样式配置为 b3。deepseek_reference_peak_cny 仅为 B2 的自定义显示参考，B3不使用。

## 验证与导出

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe export_visual_review.py --style b3
.\.venv\Scripts\python.exe preview_b3_samples.py
```

导出会重新读取真实额度，不连接蓝牙；导出图像可能包含真实余额和用量，不应随源代码上传。测试样本均为明确标注的合成数据。

## 来源与说明

蓝牙协议改写自 [PixooCtrl](https://github.com/ferzkopp/PixooCtrl)，保留 MIT 许可 LICENSE-PixooCtrl。OpenCode 非官方接口结构参考 [opencode-go-usage](https://github.com/and7ey/opencode-go-usage)，Codex 使用本机 app-server 协议，DeepSeek 使用官方余额接口。第三方来源及离线日历来源随文件保留。

本仓库不含个人配置、日志、备份、真实额度图片、API Key、令牌或虚拟环境。完整中文操作见使用说明.txt。尚未在所有设备上验证长期运行和睡眠唤醒恢复；硬件发送成功仍需目视确认。
