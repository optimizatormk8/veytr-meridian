---
title: 故障排除
description: 常见问题、解决方案和诊断工具。
order: 6
section: guides
---

## 使用哪种工具

```
安装前               → meridian preflight IP
  "这个服务器是否适合 Meridian？"

安装后，无法连接 → meridian test IP
  "从我所在的位置代理是否可达？"

安装后，出现问题 → meridian doctor IP
  "收集所有内容用于调试。"
```

添加 `--ai` 到 preflight 或 doctor 以获得 AI 就绪的诊断提示。

## 完全无法连接

### 端口 443 不可达

**原因：**
1. 云提供商防火墙 / 安全组阻止了入站端口 443
2. ISP 或网络完全阻止服务器 IP
3. 服务器已关闭或代理未运行
4. 服务器上的 UFW 不允许端口 443

**修复：**
1. 检查云提供商控制台 — 确保入站端口 443/TCP 被允许
2. 从不同的网络尝试（移动数据、另一个 Wi-Fi）
3. SSH 进入并检查：`docker ps`（3x-ui 是否运行？），`ss -tlnp sport = :443`
4. 检查 UFW：`ufw status` — 应该显示 443/tcp ALLOW

### TLS 握手失败

**原因：**
1. Xray 未在 Docker 容器内运行
2. 端口 443 被另一个服务占用
3. Reality SNI 目标从服务器无法访问

**修复：**
1. 检查 Xray：`docker logs 3x-ui --tail 20`
2. 检查端口：`ss -tlnp sport = :443` — 应该是 haproxy
3. 测试 SNI：`meridian preflight IP`

### 域名无法访问

**原因：**
1. DNS 未指向服务器 IP
2. Caddy 未运行或未能获取 TLS 证书
3. HAProxy 未正确路由域 SNI

**修复：**
1. 检查 DNS：`dig +short yourdomain.com @8.8.8.8`
2. 检查 Caddy：`systemctl status caddy`
3. 检查 HAProxy：`/etc/haproxy/haproxy.cfg`

## 连接在几秒钟后中断

**原因：**
1. 客户端和服务器之间的系统时钟偏差 >30 秒
2. 网络路径上的 MTU 问题
3. ISP 重置长期 TLS 会话

**修复：**
1. 服务器：`timedatectl set-ntp true`。客户端：启用自动日期/时间
2. 尝试不同的网络
3. 使用 WSS/CDN 连接（域名模式）

## 设置失败

### 端口 443 冲突

另一个服务（Apache、Nginx）正在使用端口 443。停止它或使用干净的服务器。`meridian preflight` 会告诉您什么在使用该端口。

### Docker 安装失败

来自 distro repos 的冲突 Docker 包。Meridian 会自动删除它们，但如果 Docker 已经运行有容器，它会跳过以避免中断。

### SSH 连接错误

手动测试 SSH：`ssh root@SERVER_IP`。确保您有基于密钥的访问。如果不是 root，请使用 `--user` 标志。

## 曾经可以工作，现在停止了

**最常见的原因：** 服务器 IP 被阻止。这在被审查的地区很常见。

**修复：**
1. 运行 `meridian test IP` — 如果 TCP 失败，该 IP 可能被阻止
2. 使用 WSS/CDN 链接（域名模式）
3. 部署新服务器：获取新 IP 并重新运行 `meridian deploy`

其他原因：
- 服务器重启且 Docker 未自动启动 → `docker start 3x-ui`
- 磁盘已满 → `df -h /`、`docker system prune -af`

## 速度缓慢

1. 选择地理位置更近的服务器（芬兰、荷兰、瑞典用于欧洲/中东）
2. 检查服务器负载：`htop` 或 `uptime`
3. 尝试 WSS/CDN 链接 — 通过 Cloudflare 的路由可能更好
4. 验证 BBR 是否启用：`sysctl net.ipv4.tcp_congestion_control`

**不要** 在同一服务器上运行其他协议（OpenVPN、WireGuard）— 这会标记该 IP。

## AI 动力帮助

```
meridian doctor --ai
```

将诊断提示复制到您的剪贴板以与任何 AI 助手一起使用。

或为 [GitHub issue](https://github.com/uburuntu/meridian/issues) 收集诊断：

```
meridian doctor
```
