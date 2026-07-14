import os
import re
import subprocess
import tempfile
import uuid
import shutil

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---- Configuration (set these as environment variables on EC2) ----
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "code-runner-web-app")
S3_REGION = os.environ.get("AWS_REGION", "ap-south-1")
EXECUTION_TIMEOUT = int(os.environ.get("EXECUTION_TIMEOUT", "10"))  # seconds

s3_client = boto3.client("s3", region_name=S3_REGION)


def upload_to_s3(local_path, s3_key):
    """Upload a file to S3. Returns (success, message_or_url)."""
    try:
        s3_client.upload_file(local_path, S3_BUCKET, s3_key)
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        return True, url
    except NoCredentialsError:
        return False, "No AWS credentials found on this instance (attach an IAM role with S3 access)."
    except ClientError as e:
        return False, str(e)


def extract_java_class_name(code: str) -> str:
    """Java files must be named after their public class."""
    match = re.search(r'public\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    match = re.search(r'class\s+(\w+)', code)
    if match:
        return match.group(1)
    return "Main"


def run_python(code: str):
    work_dir = tempfile.mkdtemp(prefix="pyrun_")
    file_name = f"script_{uuid.uuid4().hex[:8]}.py"
    file_path = os.path.join(work_dir, file_name)

    with open(file_path, "w") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["python3", file_name],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=work_dir,
        )
        if result.returncode == 0:
            return True, result.stdout, file_path, file_name, work_dir
        return False, (result.stderr or result.stdout), None, file_name, work_dir
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {EXECUTION_TIMEOUT} seconds", None, file_name, work_dir


def run_java(code: str):
    work_dir = tempfile.mkdtemp(prefix="javarun_")
    class_name = extract_java_class_name(code)
    file_name = f"{class_name}.java"
    file_path = os.path.join(work_dir, file_name)

    with open(file_path, "w") as f:
        f.write(code)

    try:
        compile_result = subprocess.run(
            ["javac", file_name],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=work_dir,
        )
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out", None, file_name, work_dir

    if compile_result.returncode != 0:
        return False, compile_result.stderr, None, file_name, work_dir

    try:
        run_result = subprocess.run(
            ["java", "-cp", work_dir, class_name],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=work_dir,
        )
        if run_result.returncode == 0:
            return True, run_result.stdout, file_path, file_name, work_dir
        return False, (run_result.stderr or run_result.stdout), None, file_name, work_dir
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {EXECUTION_TIMEOUT} seconds", None, file_name, work_dir


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json(silent=True) or {}
    language = data.get("language")
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"success": False, "message": "No code provided.", "output": ""}), 400

    if language == "python":
        success, output, file_path, file_name, work_dir = run_python(code)
    elif language == "java":
        success, output, file_path, file_name, work_dir = run_java(code)
    else:
        return jsonify({"success": False, "message": "Unsupported language.", "output": ""}), 400

    try:
        if success:
            s3_key = f"{language}/{file_name}"
            uploaded, info = upload_to_s3(file_path, s3_key)
            if uploaded:
                return jsonify({
                    "success": True,
                    "message": f"Code executed successfully. File stored to S3 as '{s3_key}'.",
                    "s3_url": info,
                    "output": output,
                })
            return jsonify({
                "success": True,
                "message": f"Code executed successfully, but S3 upload failed: {info}",
                "output": output,
            })
        else:
            return jsonify({
                "success": False,
                "message": "Execution failed. File was NOT stored to S3.",
                "output": output,
            })
    finally:
        # clean up temp working directory
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)