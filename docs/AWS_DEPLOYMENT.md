# AWS Deployment Instructions

Step-by-step guide to run this Flask + PostgreSQL Docker application on **Amazon Web Services (AWS)**.

This guide covers the recommended path (**EC2 + Docker Compose**) used by most teams for a first AWS deployment of this project. Optional sections cover HTTPS, RDS, and ECS.

---

## What you are deploying

```
Internet → EC2 (Nginx :80 or :8080) → Flask/Gunicorn → PostgreSQL (container volume)
```

| Container | Role |
|-----------|------|
| `nginx` | Public entry point, static files |
| `web` | Flask app (Gunicorn) |
| `db` | PostgreSQL 16 with persistent volume |

---

## Prerequisites

Before you start, you need:

- [ ] An **AWS account** with billing enabled
- [ ] **AWS CLI** installed locally ([install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- [ ] **SSH key pair** created in EC2 (`.pem` file)
- [ ] This project code available (Git repo, zip, or SCP from your machine)
- [ ] Basic familiarity with SSH and Docker

---

## Part 1 — Prepare the project locally

### Step 1: Create production environment file

On your local machine:

```powershell
cd c:\AWS_Docker
copy .env.example .env
```

Edit `.env` and set **strong production values**:

```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=<long-random-password>
POSTGRES_DB=appdb

SECRET_KEY=<long-random-secret-at-least-32-chars>
APP_ENV=production

# Use port 80 on EC2 for direct web access (or keep 8080)
NGINX_PORT=80
```

Generate secrets (PowerShell example):

```powershell
# Random secret key (copy output into .env)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object {[char]$_})
```

> **Important:** Never commit `.env` to Git. It is already listed in `.gitignore`.

### Step 2: Verify the app runs locally (optional but recommended)

```powershell
docker compose up --build -d
```

Open http://localhost:8080, log in with `admin` / `password`, confirm Items and Database pages work.

```powershell
docker compose down
```

### Step 3: Push code to a Git repository (recommended)

```powershell
git init
git add .
git commit -m "Initial Flask Docker app"
git remote add origin <your-repo-url>
git push -u origin main
```

Alternatively, zip the project and upload it to the EC2 instance later.

---

## Part 2 — Create AWS infrastructure

### Step 4: Choose an AWS region

Pick a region close to your users (examples: `us-east-1`, `us-west-2`, `ap-southeast-1`). Use the same region for all resources below.

### Step 5: Create a VPC security group

In **AWS Console → EC2 → Security Groups → Create security group**:

| Setting | Value |
|---------|-------|
| Name | `flask-app-sg` |
| Description | Flask Docker app |
| VPC | Default VPC (fine for testing) |

**Inbound rules:**

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | My IP | SSH access to EC2 |
| HTTP | 80 | 0.0.0.0/0 | Web app (if `NGINX_PORT=80`) |
| Custom TCP | 8080 | 0.0.0.0/0 | Web app (if `NGINX_PORT=8080`) |

> Do **not** expose PostgreSQL port 5432 to the internet. The database stays on the Docker internal network only.

**Outbound rules:** Allow all (default).

### Step 6: Create or select an EC2 key pair

**EC2 → Key Pairs → Create key pair**

- Name: `flask-app-key`
- Type: RSA
- Format: `.pem` (Linux/Mac) or `.ppk` (PuTTY on Windows)

Save the file securely. You need it to SSH into the instance.

### Step 7: Launch an EC2 instance

**EC2 → Instances → Launch instance**

| Setting | Recommended value |
|---------|-------------------|
| Name | `flask-docker-app` |
| AMI | **Amazon Linux 2023** or **Ubuntu 22.04 LTS** |
| Instance type | `t3.small` (minimum; `t3.medium` for heavier use) |
| Key pair | `flask-app-key` |
| Security group | `flask-app-sg` |
| Storage | 20–30 GB gp3 (minimum; increase if storing lots of DB data) |

Click **Launch instance**. Wait until status is **Running**.

### Step 8: Assign an Elastic IP (recommended)

A static public IP prevents the URL from changing after reboot.

1. **EC2 → Elastic IPs → Allocate Elastic IP address**
2. Select the new IP → **Actions → Associate Elastic IP address**
3. Choose your EC2 instance

Note the **Elastic IP address** — this is your server IP (e.g. `54.123.45.67`).

---

## Part 3 — Install Docker on EC2

### Step 9: Connect to EC2 via SSH

**Amazon Linux 2023:**

```bash
ssh -i flask-app-key.pem ec2-user@<ELASTIC_IP>
```

**Ubuntu:**

```bash
ssh -i flask-app-key.pem ubuntu@<ELASTIC_IP>
```

### Step 10: Install Docker and Docker Compose

**Amazon Linux 2023:**

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Docker Compose plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Log out and back in for group membership
exit
```

SSH back in, then verify:

```bash
docker --version
docker compose version
```

**Ubuntu 22.04:**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
exit
```

SSH back in and verify Docker works.

---

## Part 4 — Deploy the application

### Step 11: Copy project files to EC2

**Option A — Git clone (recommended):**

```bash
cd ~
git clone <your-repo-url> AWS_Docker
cd AWS_Docker
```

**Option B — SCP from your Windows machine:**

```powershell
scp -i flask-app-key.pem -r c:\AWS_Docker ec2-user@<ELASTIC_IP>:~/AWS_Docker
```

Then on EC2:

```bash
cd ~/AWS_Docker
```

### Step 12: Create `.env` on the server

```bash
cp .env.example .env
nano .env
```

Set the same production values as in Part 1 (strong passwords, `SECRET_KEY`, `NGINX_PORT=80`).

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

### Step 13: Build and start containers

```bash
docker compose up --build -d
```

Check status:

```bash
docker compose ps
docker compose logs -f web
```

You should see migrations run, admin user seeded, and Gunicorn started.

### Step 14: Open the app in your browser

```
http://<ELASTIC_IP>/
```

Log in with default credentials:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `password` |

> **Change the admin password immediately** after first login (via Database Manager → `users` table, or create a new admin and delete the old one).

---

## Part 5 — Post-deployment configuration

### Step 15: Enable auto-start on reboot

Docker Compose `restart: unless-stopped` is already set. Ensure Docker starts on boot:

```bash
sudo systemctl enable docker
```

After an EC2 reboot, containers should come back automatically. Verify with:

```bash
docker compose ps
```

### Step 16: Configure a domain name (optional)

If you own a domain in **Route 53**:

1. **Route 53 → Hosted zones → your domain → Create record**
2. Type: **A**
3. Value: your **Elastic IP**
4. Save

Update `nginx/nginx.conf` `server_name` from `localhost` to your domain if needed, then:

```bash
docker compose restart nginx
```

### Step 17: Add HTTPS with Application Load Balancer (recommended for production)

For production traffic you should use HTTPS:

1. Request a certificate in **AWS Certificate Manager (ACM)** for your domain
2. Create an **Application Load Balancer (ALB)**:
   - Listener 443 (HTTPS) → target group → EC2 instance port 80
   - Listener 80 → redirect to 443
3. Point Route 53 A record (alias) to the ALB
4. Update EC2 security group: allow HTTP/HTTPS from ALB security group only (remove open `0.0.0.0/0` if possible)

### Step 18: Database backups

The PostgreSQL data lives in Docker volume `postgres_data`.

**Manual backup on EC2:**

```bash
cd ~/AWS_Docker
docker compose exec db pg_dump -U appuser appdb > backup_$(date +%Y%m%d).sql
```

**Copy backup to your machine:**

```powershell
scp -i flask-app-key.pem ec2-user@<ELASTIC_IP>:~/AWS_Docker/backup_*.sql .
```

**Automate with a cron job on EC2:**

```bash
crontab -e
```

Add (daily backup at 2 AM):

```
0 2 * * * cd /home/ec2-user/AWS_Docker && docker compose exec -T db pg_dump -U appuser appdb > /home/ec2-user/backups/appdb_$(date +\%Y\%m\%d).sql
```

Create the backups folder first: `mkdir -p ~/backups`

---

## Part 6 — Production hardening checklist

Before going live with real users:

- [ ] Change `admin` / `password` default login
- [ ] Set strong `SECRET_KEY` and `POSTGRES_PASSWORD` in `.env`
- [ ] Use `NGINX_PORT=80` or ALB; do not expose port 5432 publicly
- [ ] Restrict SSH (port 22) to your IP only in the security group
- [ ] Enable HTTPS via ALB + ACM certificate
- [ ] Set up automated DB backups (cron + S3 upload optional)
- [ ] Monitor disk usage on EC2 (PostgreSQL volume grows over time)
- [ ] Consider **Amazon RDS** instead of container PostgreSQL for production (see below)

---

## Part 7 — Upgrade path: Amazon RDS (optional)

For production workloads, move PostgreSQL from a Docker container to **Amazon RDS**:

1. **RDS → Create database**
   - Engine: PostgreSQL 16
   - Template: Production or Dev/Test
   - DB instance class: `db.t3.micro` (dev) or larger (prod)
   - Master username/password: note these values
   - VPC: same as EC2
   - Public access: **No**

2. Update EC2 security group to allow outbound to RDS; RDS security group allows inbound 5432 from EC2 security group.

3. Update `.env` on EC2:

   ```env
   DATABASE_URL=postgresql://<user>:<password>@<rds-endpoint>:5432/appdb
   ```

4. Remove or disable the `db` service in a production override file (`docker-compose.prod.yml`), then:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

5. Run migrations against RDS:

   ```bash
   docker compose exec web flask db upgrade
   ```

---

## Part 8 — Alternative: Amazon ECS (optional)

For larger scale or CI/CD pipelines:

| Step | Action |
|------|--------|
| 1 | Push Docker image to **Amazon ECR** |
| 2 | Create **ECS cluster** (Fargate or EC2 launch type) |
| 3 | Define task definitions for `web` and `nginx` |
| 4 | Use **RDS** for PostgreSQL |
| 5 | Place **ALB** in front of the ECS service |
| 6 | Store secrets in **AWS Secrets Manager** (`SECRET_KEY`, DB password) |

This requires splitting the current `docker-compose.yml` into ECS task definitions — suitable after the EC2 proof-of-concept is working.

---

## Common operations on AWS

| Task | Command (on EC2 in project folder) |
|------|-------------------------------------|
| View logs | `docker compose logs -f web` |
| Restart app | `docker compose restart web nginx` |
| Rebuild after code update | `git pull && docker compose up --build -d` |
| Stop app | `docker compose down` |
| Stop and wipe DB | `docker compose down -v` |
| Check health | `curl http://localhost/health` |
| Shell into web container | `docker compose exec web bash` |
| Run migration | `docker compose exec web flask db upgrade` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cannot reach app in browser | Check EC2 security group allows port 80/8080; verify `docker compose ps` shows nginx running |
| `web` container restarting | Run `docker compose logs web`; often DB not ready or migration error |
| Permission denied on SSH | `chmod 400 flask-app-key.pem` on your local key file |
| Docker permission denied on EC2 | Log out/in after `usermod -aG docker`; or use `sudo docker compose ...` |
| Out of disk space | `docker system prune -a`; increase EBS volume size in EC2 console |
| Forgot admin password | Connect to DB: `docker compose exec db psql -U appuser appdb` and update `users` table, or re-seed |

---

## Quick reference

| Item | Value |
|------|-------|
| App URL | `http://<ELASTIC_IP>/` or `https://your-domain.com` |
| Default login | `admin` / `password` (change immediately) |
| Health check | `/health` |
| Project folder on EC2 | `~/AWS_Docker` |
| DB volume | Docker volume `aws_docker_postgres_data` |

---

## Related documentation

- [Project Requirements](PROJECT_REQUIREMENTS.md)
- [Tech Stack](TECH_STACK.md)
- [Features & Functions](FEATURES.md)
- [Session Summary](SESSION_SUMMARY.md)
- [README](../README.md) — local Docker quick start
