---
title: 客户端管理
description: 添加、列出和删除客户端访问密钥。
order: 5
section: guides
---

## 添加客户端

```
meridian client add alice
```

每个客户端都获得自己的唯一连接密钥。该命令生成：
- 在终端中显示的 **QR 码**
- 本地保存的 **HTML 连接页面**
- 一个 **可共享的 URL**（如果启用了服务器托管页面）

## 列出客户端

```
meridian client list
```

显示所有客户端及其协议连接（Reality、XHTTP、WSS）。

## 删除客户端

```
meridian client remove alice
```

立即撤销访问权限。客户端的 UUID 将从服务器上的所有入站中删除。

## 多服务器

使用 `--server` 来针对特定的命名服务器：

```
meridian client add alice --server finland
```

如果您只有一个服务器，它会自动选择。

## 工作原理

客户端名称映射到带有协议前缀的 3x-ui `email` 字段：
- `reality-alice` — Reality 入站
- `xhttp-alice` — XHTTP 入站
- `wss-alice` — WSS 入站（域名模式）

每个客户端在服务器上所有入站中获得唯一的 UUID。
