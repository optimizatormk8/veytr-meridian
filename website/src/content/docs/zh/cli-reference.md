---
title: CLI 参考
description: Meridian CLI 所有命令和标志的完整参考。
order: 8
section: reference
---

## 命令

### meridian deploy

部署代理服务器到 VPS。

```
meridian deploy [IP] [flags]
```

| 标志 | 默认值 | 描述 |
|------|---------|-------------|
| `--sni HOST` | www.microsoft.com | Reality 伪装的网站 |
| `--domain DOMAIN` | (无) | 启用域名模式和 CDN 回退 |
| `--email EMAIL` | (无) | TLS 证书的电子邮件 |
| `--xhttp / --no-xhttp` | 启用 | XHTTP 传输 |
| `--name NAME` | default | 第一个客户端的名称 |
| `--user USER` | root | SSH 用户 |
| `--yes` | | 跳过确认提示 |

### meridian client

管理客户端访问密钥。

```
meridian client add NAME [--server NAME]
meridian client list [--server NAME]
meridian client remove NAME [--server NAME]
```

### meridian server

管理已知服务器。

```
meridian server add [IP]
meridian server list
meridian server remove NAME
```

### meridian preflight

预检查服务器验证。测试 SNI、端口、DNS、OS、磁盘、ASN，无需安装任何内容。

```
meridian preflight [IP] [--ai] [--server NAME]
```

### meridian scan

使用 RealiTLScanner 在服务器网络上查找最优 SNI 目标。

```
meridian scan [IP] [--server NAME]
```

### meridian test

从客户端设备测试代理可达性。无需 SSH。

```
meridian test [IP] [--server NAME]
```

### meridian doctor

收集系统诊断信息以便调试。别名：`meridian rage`。

```
meridian doctor [IP] [--ai] [--server NAME]
```

### meridian teardown

从服务器移除代理。

```
meridian teardown [IP] [--server NAME] [--yes]
```

### meridian update

将 CLI 更新到最新版本。

```
meridian update
```

### meridian --version

显示 CLI 版本。

```
meridian --version
meridian -v
```

## 全局标志

| 标志 | 描述 |
|------|-------------|
| `--server NAME` | 目标特定的已命名服务器 |

## 服务器解析

需要服务器的命令按照此优先级：
1. 显式 IP 参数
2. `--server NAME` 标志
3. 本地模式检测（在服务器本身运行）
4. 单个服务器自动选择（如果只保存了一个）
5. 交互提示
