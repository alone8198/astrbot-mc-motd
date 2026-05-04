# AstrBot Minecraft MOTD 查询插件

查询 Minecraft 服务器 MOTD 信息的 AstrBot 插件，支持 **Java 版** 和 **基岩版**。

## 安装

将插件目录放入 AstrBot 的 `data/plugins/` 下，或在 AstrBot WebUI 插件市场中搜索安装。

插件依赖 `mcstatus`，安装后会自动通过 `requirements.txt` 安装。

## 使用

```
/motd <服务器IP>[:端口] <je/be>
```

| 参数 | 说明 |
|------|------|
| 服务器IP | 域名或 IP 地址，可附带端口（如 `127.0.0.1:25566`） |
| je/be | 可选，默认 `je`。`je` = Java 版，`be` = 基岩版 |

### 默认端口

| 版本 | 默认端口 |
|------|----------|
| Java 版 (je) | 25565 |
| 基岩版 (be) | 19132 |

### 示例

```
/motd mc.hypixel.net je
/motd play.example.com:25565
/motd 127.0.0.1 be
/motd [::1]:25565 je
```

### 返回信息

```
══ Minecraft 服务器状态 ══
  服务器: mc.hypixel.net:25565
  版本: Java Edition 1.8-1.21
  延迟: 42.3ms
  玩家: 48392/200000
  MOTD: Hypixel Network [1.8-1.21]
══════════════════════════
```

## 支持功能

- Java 版 / 基岩版服务器查询
- IPv4 / IPv6 / 域名地址解析
- MOTD JSON 文本组件解析（支持 `extra` 嵌套）
- Minecraft 格式代码（`§`）自动清除
- 友好的中文错误提示（超时、拒绝连接、DNS 解析失败等）

## 依赖

- Python >= 3.8
- [mcstatus](https://github.com/py-mine/mcstatus) >= 11.0.0
