# PythonAnywhere 自动续期指南

本指南介绍如何使用 `scripts/renew_pa.py` 脚本自动延续 PythonAnywhere 免费 Web 应用的有效期。

## ⚠️ 风险提示

PythonAnywhere 要求免费用户手动登录以确认账户活跃度。使用脚本自动化此过程可能违反其服务条款（ToS）。请自行承担风险。

## 方法一：本地运行

您可以随时在本地运行脚本来手动续期，而无需登录浏览器。

1. 确保安装了 `requests` 库：
   ```bash
   pip install requests
   ```

2. 设置环境变量并运行：
   ```bash
   export PA_USERNAME="your_username"
   export PA_PASSWORD="your_password"
   # 如果您的域名不是 username.pythonanywhere.com，请设置 PA_DOMAIN
   # export PA_DOMAIN="www.yourdomain.com"
   
   python scripts/renew_pa.py
   ```

## 方法二：GitHub Actions 自动运行

您可以设置 GitHub Actions 每月自动运行一次该脚本。

1. 在 GitHub 仓库页面，点击 **Settings** -> **Secrets and variables** -> **Actions**。
2. 点击 **New repository secret**，添加以下密钥：
   
   | Name | Value | 说明 |
   | :--- | :--- | :--- |
   | `PA_USERNAME` | 您的 PythonAnywhere 用户名 | 必填 |
   | `PA_PASSWORD` | 您的 PythonAnywhere 密码 | 必填 |
   | `PA_DOMAIN` | `username.pythonanywhere.com` | 选填（如果使用默认域名可不填）|

3. 配置完成后，Workflow 会在每月的 1 号和 15 号自动运行。
4. 您也可以在 **Actions** 选项卡中手动触发 `Renew PythonAnywhere WebApp` 工作流来测试是否配置成功。

## 脚本位置

- 脚本：`scripts/renew_pa.py`
- Workflow 配置：`.github/workflows/renew_pa.yml`
