# Cloud Code Runner (Python + Java → EC2 → S3)

A minimal web app: paste Python or Java code in the browser, it runs on the
EC2 server, and — **only if it runs successfully** — the source file is
uploaded to S3 with its correct extension (`.py` / `.java`). The UI shows a
success message with the program's output, or an error message if it failed
(nothing is uploaded on failure).

Tested locally end-to-end (success + error cases, both languages) before
handing off.

## Project structure
```
code-runner-app/
├── app.py                 # Flask backend: run code, upload to S3
├── requirements.txt
├── templates/
│   └── index.html          # UI
└── static/
    └── style.css
```

## 1. Create the S3 bucket
```bash
aws s3 mb s3://YOUR-BUCKET-NAME --region us-east-1
```

## 2. Launch the EC2 instance
- AMI: **Ubuntu 24.04 LTS**
- Instance type: `t2.micro` (free tier is fine)
- Security group: allow inbound **TCP 22** (SSH, your IP) and **TCP 5000**
  (or 80 if you put Nginx in front)

### IAM role (important — don't use access keys on the instance)
Create an IAM role with a policy like this and attach it to the instance:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

## 3. SSH in and install dependencies
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

sudo apt update
sudo apt install -y python3-pip python3-venv default-jdk-headless git
java -version   # sanity check javac/java exist
```

## 4. Get the app onto the instance
Copy the `code-runner-app` folder to the instance (e.g. `scp -r`, or push it
to a git repo and `git clone` it), then:
```bash
cd code-runner-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Configure environment variables
```bash
export S3_BUCKET_NAME=YOUR-BUCKET-NAME
export AWS_REGION=us-east-1
```
(Add these to `~/.bashrc` or, better, to the systemd service below so they
persist.)

## 6. Run it

**Quick test:**
```bash
python3 app.py
# visit http://<EC2_PUBLIC_IP>:5000
```

**Production (gunicorn + systemd), recommended:**
```bash
sudo tee /etc/systemd/system/coderunner.service > /dev/null <<'EOF'
[Unit]
Description=Cloud Code Runner
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/code-runner-app
Environment="S3_BUCKET_NAME=YOUR-BUCKET-NAME"
Environment="AWS_REGION=us-east-1"
ExecStart=/home/ubuntu/code-runner-app/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now coderunner
sudo systemctl status coderunner
```

Visit `http://<EC2_PUBLIC_IP>:5000` in your browser.

## How it works
1. UI sends `{language, code}` to `POST /run`.
2. Backend writes the code to a temp file (`.py`, or `<PublicClass>.java`),
   then runs it with `python3` or `javac`+`java` (10s timeout).
3. **Exit code 0 (and, for Java, successful compile)** → file is uploaded to
   `s3://BUCKET/python/...` or `s3://BUCKET/java/...`, and the UI shows a
   success message plus the program's stdout.
4. **Any error / non-zero exit / compile failure** → nothing is uploaded,
   and the UI shows the error message (stderr) instead.
5. Temp files/directories are always cleaned up afterward.

## Security note
This app executes arbitrary code with `subprocess`, which is fine for a demo
or trusted internal tool but is **not sandboxed** (no container/user
isolation, no resource limits beyond a timeout). Don't expose it publicly
without adding real isolation (e.g. run inside Docker with `--network none`
and a restricted user, or use AWS Lambda/Fargate per-execution containers).