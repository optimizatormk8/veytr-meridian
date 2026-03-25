---
title: امنیت
description: طراحی امنیت، گزارش آسیب‌پذیری، و دامنه.
order: 11
section: reference
---

## گزارش آسیب‌پذیری‌های امنیتی

اگر یک آسیب‌پذیری امنیتی در Meridian کشف کنید:

1. **یک issue عمومی باز نکنید**
2. ایمیل به نگاهبان یا استفاده کنید از [GitHub Security Advisories](https://github.com/uburuntu/meridian/security/advisories/new)
3. مراحل تکرار و تأثیر احتمالی را شامل کنید

ما بعد از 48 ساعت پاسخ دهیم و گزارش‌کنندگان را در اصلاحیه به‌رسمی تشکر می‌کنیم.

## طراحی امنیت

- **اعتبارات**: با اجازه‌های `0600` ذخیره می‌شوند، اسرار هرگز از طریق دستورات shell بدون `shlex.quote()` منتقل نمی‌شوند، از خروجی `meridian doctor` حذف می‌شوند
- **دسترسی پنل**: توسط Caddy در یک مسیر HTTPS مخفی reverse-proxy می‌شود در تمام حالات — هیچ تونل SSH لازم نیست
- **SSH**: احراز هویت رمز رمز به طور پیش‌فرض غیرفعال است
- **Firewall**: UFW با deny-all-incoming پیکربندی می‌شود، فقط پورت‌های 22، 80، و 443 باز می‌شوند
- **Docker**: تصویر 3x-ui به نسخه تست‌شده‌ای پین شده‌اند
- **TLS**: Caddy گواهینامه‌ها را به طور خودکار از طریق Let's Encrypt مدیریت می‌کند

## دامنه

Meridian سرورهای proxy را پیکربندی می‌کند — پروتکل‌های رمزنگاری را اجرا نمی‌کند. امنیت زیرین بستگی دارد به:

- [Xray-core](https://github.com/XTLS/Xray-core) — پروتکل VLESS+Reality
- [3x-ui](https://github.com/MHSanaei/3x-ui) — پنل مدیریت
- [Caddy](https://github.com/caddyserver/caddy) — خاتمه TLS
- [HAProxy](https://www.haproxy.org/) — مسیریابی SNI
