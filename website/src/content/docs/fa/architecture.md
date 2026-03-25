---
title: معماری سیستم
description: معماری سیستم، جریان ترافیق، و توپولوژی سرویس.
order: 9
section: reference
---

## پشته فناوری

- **VLESS+Reality** (Xray-core) — پروتکل پروکسی که خود را به عنوان یک وب‌سایت TLS معتبر جا می‌زند. سانسورچی‌هایی که سرور را بررسی می‌کنند یک گواهی واقعی (مثلاً از microsoft.com) می‌بینند. فقط کلاینت‌هایی با کلید خصوصی صحیح می‌توانند متصل شوند.
- **3x-ui** — پنل وب برای مدیریت Xray، به صورت کانتینر Docker مستقر شده. Meridian آن را کاملاً از طریق REST API مدیریت می‌کند.
- **HAProxy** — روتر TCP سطح SNI روی پورت 443. ترافیک را بر اساس نام میزبان SNI بدون پایان دادن TLS مسیریابی می‌کند.
- **Caddy** — پروکسی معکوس با TLS خودکار. در حالت مستقل، گواهی Let's Encrypt IP را از طریق پروفایل ACME `shortlived` (اعتبار 6 روزه) درخواست می‌کند. صفحات اتصال را ارائه می‌دهد، پنل را پروکسی معکوس می‌کند و ترافیق XHTTP/WSS را به Xray پروکسی می‌کند.
- **Docker** — 3x-ui (که شامل Xray است) را اجرا می‌کند. تمام ترافیق پروکسی از طریق کانتینر عبور می‌کند.
- **Provisioner پایتون خالص** — `src/meridian/provision/` مراحل استقرار را از طریق SSH اجرا می‌کند. هر مرحله `(conn, ctx)` دریافت و `StepResult` برمی‌گرداند.
- **uTLS** — اثر انگشت TLS Client Hello کروم را تقلید می‌کند و اتصالات را از ترافیق واقعی مرورگر غیرقابل تشخیص می‌سازد.

## توپولوژی سرویس

### حالت Standalone (بدون دامنه)

```mermaid
flowchart TD
    Internet((Internet)) -->|Port 443| HAProxy[HAProxy<br>SNI Router]
    HAProxy -->|"SNI = reality_sni"| Xray["Xray Reality<br>:10443"]
    HAProxy -->|"SNI = server IP"| Caddy["Caddy TLS<br>:8443"]
    Caddy -->|/info-path| Page[Connection Page]
    Caddy -->|/panel-path| Panel[3x-ui Panel]
    Caddy -->|/xhttp-path| XrayXHTTP["Xray XHTTP<br>localhost"]
    Internet -->|Port 80| CaddyACME["Caddy<br>ACME challenges"]
```

HAProxy TLS را تعریف نمی‌کند. آن SNI hostname را از TLS Client Hello می‌خواند و جریان TCP خام را به backend مناسب منتقل می‌کند.

Caddy گواهینامه IP Let's Encrypt را از طریق پروفایل ACME `shortlived` درخواست می‌کند (اعتبار 6 روز، تمدید خودکار). اگر صدور گواهینامه IP پشتیبانی نشود، به self-signed بازمی‌گردد.

XHTTP روی یک پورت localhost-only اجرا می‌شود و توسط Caddy reverse-proxy می‌شود — هیچ پورت خارجی اضافی노출نمی‌شود.

### حالت Domain

```mermaid
flowchart TD
    Internet((Internet)) -->|Port 443| HAProxy[HAProxy<br>SNI Router]
    HAProxy -->|"SNI = reality_sni"| Xray["Xray Reality<br>:10443"]
    HAProxy -->|"SNI = domain"| Caddy["Caddy TLS<br>:8443"]
    Caddy -->|/info-path| Page[Connection Page]
    Caddy -->|/panel-path| Panel[3x-ui Panel]
    Caddy -->|/xhttp-path| XrayXHTTP["Xray XHTTP<br>localhost"]
    Caddy -->|/ws-path| XrayWSS["Xray WSS<br>localhost"]
    Internet -->|Port 80| CaddyACME["Caddy<br>ACME challenges"]
    Internet -.->|"CDN (Cloudflare)"| Caddy
```

حالت دامنه VLESS+WSS را به عنوان مسیر fallback CDN اضافه می‌کند. ترافیک از طریق CDN Cloudflare با WebSocket جریان می‌یابد، که اتصال حتی اگر IP سرور مسدود شود کار می‌کند.

### توپولوژی Relay

```mermaid
flowchart LR
    Client([Client]) -->|Port 443| Relay["Relay<br>(Realm TCP)"]
    Relay -->|Port 443| Exit["Exit Server<br>(abroad)"]
    Exit --> Internet((Internet))
```

Relay یک دستگاه ارسال TCP سطح ۴ است که ترافیک خام را از کلاینت به سرور خروجی منتقل می‌کند. تمامی رمزگذاری بین کلاینت و سرور خروجی انجام می‌شود، relay هرگز plaintext را نمی‌بیند. این معماری امکان استفاده از نقاط ورودی داخلی (عادی‌تر، کمتر محدود) را فراهم می‌کند و سرور خروجی را در خارج از کشور قرار می‌دهد.

## نحوه کار پروتکل Reality

1. سرور یک **keypair x25519** تولید می‌کند. کلید عمومی با کلاینت‌ها به اشتراک گذاشته می‌شود، کلید خصوصی روی سرور می‌ماند.
2. کلاینت روی پورت 443 اتصال برقرار می‌کند با TLS Client Hello که شامل دامنه تقلبی (مثلاً `www.microsoft.com`) به عنوان SNI است.
3. برای هر ناظر، این به نظر می‌رسد یک اتصال معمولی HTTPS به microsoft.com.
4. اگر یک **prober** Client Hello خود را ارسال کند، سرور اتصال را به microsoft.com واقعی proxy می‌کند — prober یک گواهینامه معتبر می‌بیند.
5. اگر کلاینت تأیید معتبر (مشتق شده از کلید x25519) را شامل شود، سرور تونل VLESS را برقرار می‌کند.
6. **uTLS** Client Hello را بایت برای بایت یکسان با Chrome می‌سازد، شکست TLS fingerprinting را شکست می‌دهد.

## ساختار کانتینر Docker

کانتینر Docker `3x-ui` شامل:
- **پنل وب 3x-ui** — REST API روی پورت 2053 (داخلی)
- **باینری Xray** در `/app/bin/xray-linux-*` (مسیر وابسته به معماری)
- **پایگاه داده** در `/etc/x-ui/x-ui.db` (SQLite، پیکربندی‌های ورودی و کلاینت‌ها را ذخیره می‌کند)
- **پیکربندی Xray** توسط 3x-ui مدیریت می‌شود (فایل استاتیک نیست)

Meridian 3x-ui را کاملاً از طریق REST API مدیریت می‌کند:
- `POST /login` — احراز هویت (form-urlencoded، session cookie برمی‌گرداند)
- `POST /panel/api/inbounds/add` — ایجاد VLESS inbound
- `GET /panel/api/inbounds/list` — لیست inbounds (بررسی قبل از ایجاد)
- `POST /panel/setting/update` — پیکربندی تنظیمات پنل
- `POST /panel/setting/updateUser` — تغییر اعتبارنامه‌های پنل

## الگوی پیکربندی Caddy

Meridian در `/etc/caddy/conf.d/meridian.caddy` می‌نویسد (هرگز در Caddyfile اصلی). به Caddyfile اصلی یک خط اضافه می‌شود: `import /etc/caddy/conf.d/*.caddy`. این اجازه می‌دهد Meridian با پیکربندی خود کاربر همزیستی کند.

Caddy مدیریت می‌کند:
- گواهی TLS خودکار (گواهی دامنه یا Let's Encrypt IP از طریق پروفایل ACME `shortlived`)
- پروکسی معکوس برای پنل 3x-ui (در مسیر تصادفی)
- ارائه صفحات اتصال (صفحات میزبانی‌شده با URL‌های قابل اشتراک)
- پروکسی معکوس برای ترافیق XHTTP به Xray (مسیریابی بر اساس مسیر، در تمام حالت‌ها وقتی XHTTP فعال است)
- پروکسی معکوس برای ترافیق WSS به Xray (فقط حالت دامنه)

## اختصاص پورت

| پورت | سرویس | حالت |
|------|---------|------|
| 443 | HAProxy (SNI router) | همه |
| 80 | Caddy (ACME challenges) | همه |
| 10443 | Xray Reality (internal) | همه |
| 8443 | Caddy TLS (internal) | همه |
| localhost | Xray XHTTP | هنگام فعال بودن XHTTP |
| localhost | Xray WSS | حالت دامنه |
| 2053 | 3x-ui panel (internal) | همه |

پورت‌های XHTTP و WSS فقط localhost هستند — Caddy reverse-proxy آن‌ها را روی پورت 443 انجام می‌دهد.

## خط لوله Provisioning

تابع `build_setup_steps()` مراحل را بر اساس پروتکل‌ها و تنظیمات انتخاب‌شده گردآوری می‌کند. هر مرحله از طریق SSH به سرور ارسال می‌شود و نتایج آن در `ProvisionContext` ذخیره می‌شود.

| # | مرحله | هدف | ماژول |
|---|------|---------|--------|
| 1 | InstallPackages | بسته‌های OS | `provision/base.py` |
| 2 | EnableAutoUpgrades | ارتقاهای بدون نظارت | `provision/base.py` |
| 3 | SetTimezone | UTC | `provision/base.py` |
| 4 | HardenSSH | احراز هویت فقط کلید | `provision/base.py` |
| 5 | ConfigureBBR | کنترل ازدحام TCP | `provision/base.py` |
| 6 | ConfigureFirewall | UFW: 22 + 80 + 443 | `provision/base.py` |
| 7 | InstallDocker | Docker CE | `provision/docker.py` |
| 8 | Deploy3xui | container 3x-ui | `provision/docker.py` |
| 9 | ConfigurePanel | اعتبارات پنل | `provision/panel.py` |
| 10 | LoginToPanel | احراز هویت API | `provision/panel.py` |
| 11 | CreateRealityInbound | VLESS+Reality | `provision/inbound.py` |
| 12 | CreateXHTTPInbound | VLESS+XHTTP | `provision/inbound.py` |
| 13 | CreateWSSInbound | VLESS+WSS (domain) | `provision/inbound.py` |
| 14 | VerifyXray | بررسی سلامت | `provision/services.py` |
| 15 | InstallHAProxy | مسیریابی SNI | `provision/services.py` |
| 16 | InstallCaddy | TLS + reverse proxy | `provision/services.py` |
| 17 | DeployConnectionPage | QR codes + page | `provision/pwa.py` |

## چرخه حیات اعتبارات

1. **تولید**: اعتبارات تصادفی (رمز پنل، کلیدهای x25519، UUID کلاینت)
2. **ذخیره محلی**: `~/.meridian/credentials/<IP>/proxy.yml` — قبل از اعمال روی سرور ذخیره می‌شود
3. **اعمال**: رمز پنل تغییر می‌کند، inbounds ایجاد می‌شوند
4. **هماهنگی**: اعتبارات به `/etc/meridian/proxy.yml` روی سرور کپی می‌شوند
5. **بازاجرا**: از cache بارگذاری می‌شوند، دوباره تولید نمی‌شوند (idempotent)
6. **ماشین‌های متعدد**: `meridian server add IP` از سرور از طریق SSH واکشی می‌کند
7. **حذف**: از سرور و ماشین محلی حذف می‌شوند

## مکان فایل‌ها

### روی سرور
- `/etc/meridian/proxy.yml` — اعتبارنامه‌ها و لیست کلاینت‌ها
- `/etc/caddy/conf.d/meridian.caddy` — پیکربندی Caddy
- `/etc/haproxy/haproxy.cfg` — پیکربندی HAProxy
- کانتینر Docker `3x-ui` — Xray + پنل

### روی ماشین محلی
- `~/.meridian/credentials/<IP>/` — اعتبارنامه‌های کش‌شده برای هر سرور
- `~/.meridian/servers` — رجیستری سرورها
- `~/.meridian/cache/` — کش بررسی به‌روزرسانی
- `~/.local/bin/meridian` — نقطه ورود CLI (نصب‌شده از طریق uv/pipx)
