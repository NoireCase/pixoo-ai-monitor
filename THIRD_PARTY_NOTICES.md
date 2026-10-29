# 第三方来源与许可

## PixooCtrl

- 来源：https://github.com/ferzkopp/PixooCtrl
- Copyright (c) 2026 Andreas Schiffler
- 许可：MIT，全文保留于 [LICENSE-PixooCtrl](LICENSE-PixooCtrl)。
- `drivers/pixoo.py` 由其原版 Pixoo RFCOMM 连接和图像编码实现改写，保留原有署名。
- PixooCtrl 注明其协议参考来自 virtualabs/pixoo-client 等项目；本项目集成来源为 PixooCtrl。

## 接口与规则参考

- OpenCode Go 用量接口结构参考：https://github.com/and7ey/opencode-go-usage
- Codex 本机 app-server 协议：https://learn.chatgpt.com/docs/app-server
- DeepSeek 官方余额与定价文档：https://api-docs.deepseek.com/
- 中国法定假日数据的官方来源及核实日期随 `data/china_statutory_holidays.json` 保存。

以上接口解析和离线判断由本项目实现；来源说明不授予对应服务商标、账户或 API 的使用权。使用服务需自行拥有适当账户和凭据。

## 运行依赖

依赖由 `setup.ps1` 从包索引安装，发行包不捆绑其二进制文件。Pillow、keyring、pytest 及其间接依赖各自遵循上游许可证。本项目的 MIT 许可不会替换这些依赖或上游驱动的版权声明。
