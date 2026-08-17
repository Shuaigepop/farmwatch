# FarmWatch 智慧农业系统 - 部署手册

## 简介
FarmWatch 是一个结合了 LINE 机器人与 Google Gemini AI 的智慧农业管理系统，能自动收集农场任务进度、接收员工回传的照片、并透过 AI 分析农作物健康，最终在每天早晚自动产生每日汇整报告。

---

## 🚀 云端主机 (VPS) 部署教学

以下教学适用於 Ubuntu / Debian 系统环境（如 AWS EC2, GCP Compute Engine, DigitalOcean, Linode 等）。

### 1. 安装 Docker 与 Docker Compose
如果您的主机尚未安装 Docker，请执行以下指令：
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. 下载系统专案
将整个 `farmwatch` 资料夹上传至您的主机（或透过 Git Clone 下载）。
进入专案目录：
```bash
cd farmwatch
```

### 3. 环境变数设定 (.env)
在 `farmwatch` 根目录建立一个 `.env` 档案，并填入您的 API 密钥：
```bash
nano .env
```
填入以下内容：
```env
LINE_CHANNEL_SECRET=你的_LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_CHANNEL_ACCESS_TOKEN
GEMINI_API_KEY=你的_GEMINI_API_KEY
JWT_SECRET_KEY=请随机生成一段复杂的字串(例如：a1b2c3d4...)
```

### 4. 准备资料储存资料夹
为了确保伺服器重启或更新时，资料库与上传的照片不会遗失，我们需要建立本机挂载点：
```bash
mkdir -p data/uploads
touch data/farmwatch.db
```

### 5. 一键启动服务
使用 Docker Compose 启动整个系统（背景执行）：
```bash
sudo docker-compose up -d
```

### 6. 设定反向代理 (Nginx / Cloudflare)
为了让 LINE 能够呼叫您的伺服器，您需要提供一个 **HTTPS** 的网域。
推荐使用 Cloudflare Tunnel，或是安装 Nginx 搭配 Let's Encrypt 凭证将 443 Port 代理到本地的 `8000` Port。

**如果使用 Cloudflare Tunnel（最推荐且免费）：**
在主机上执行：
```bash
cloudflared tunnel --url http://localhost:8000
```
（在正式环境中，建议透过 Cloudflare Zero Trust 后台设定长期固定网域的 Tunnel）

### 7. 更新 LINE Developers Webhook URL
当您取得 HTTPS 网域后（例如 `https://your-domain.com`），请前往 LINE Developers 后台，将 Webhook URL 更改为：
> `https://your-domain.com/api/webhook/line`

---

## 🛠 系统管理与维护

- **检视伺服器 Log 纪录：**
  ```bash
  sudo docker-compose logs -f farmwatch-api
  ```
- **重启系统：**
  ```bash
  sudo docker-compose restart
  ```
- **关闭系统：**
  ```bash
  sudo docker-compose down
  ```
- **更新程式码后重新建置：**
  ```bash
  sudo docker-compose up -d --build
  ```

---

## 👨‍🌾 预设帐号密码
系统第一次启动时会自动建立预设资料：
- **老板 (Boss)**: 帐号 `admin` / 密码 `admin123`
- **主管 (Supervisor)**: 帐号 `supervisor` / 密码 `super123`
- **组长 (Leader)**: 帐号 `leader` / 密码 `leader123`

（请在上线后进入系统更改密码或删除预设帐号以保安全！）
