Cloud Code Runner (Python & Java on AWS)

Cloud Code Runner is a web-based application that allows users to write and execute Python and Java code directly from the browser. The application runs code on an AWS EC2 instance and automatically uploads only successfully executed source files (.py and .java) to Amazon S3.

🚀 Features
-Execute Python and Java code online
-Real-time code execution using Flask
-Upload successful source files to Amazon S3
-Automatic Java class detection
-Modern responsive UI
-Temporary files cleaned after execution
-CI/CD using GitHub, AWS CodeBuild & CodePipeline


☁️ AWS Services Used
Amazon EC2
Amazon S3
AWS IAM
AWS CodeBuild
AWS CodePipeline
GitHub


💻 Technologies
Python
Flask
HTML, CSS, JavaScript
Java (JDK)
Boto3
Git & GitHub
Ubuntu Linux

  📂 Project Workflow
  User
   ↓
  Web UI
   ↓
  Flask API (/run)
   ↓
  Execute Python / Java
   ↓
  Success?
  ┌───────────────┐
  │               │
  Yes             No
  │               │
  ▼               ▼
  Upload to S3   Show Error


📁 Project Structure
code-runner-app/
├── app.py
├── requirements.txt
├── buildspec.yml
├── templates/
│   └── index.html
└── static/
    └── style.css


🔐 Security
-IAM Role for S3 access
-No AWS Access Keys stored
-Only successful code is uploaded
-Temporary files removed after execution
-Execution timeout enabled


🚀 CI/CD
  GitHub Repository
        │
        ▼
  AWS CodePipeline
        │
        ▼
  AWS CodeBuild
        │
        ▼
  Build Artifacts stored in Amazon S3


📈 Future Enhancements
-Docker sandbox execution
-User authentication
-More programming languages
-DynamoDB execution history
-Auto Scaling & Load Balancer


👨‍💻 Author
Nilesh Rajendra Pardeshi

- B.Tech – Artificial Intelligence & Machine Learning
- R. C. Patel Institute of Technology, Shirpur
- AWS with Python Course Trainee (Symbiosis, Sponsored by Capgemini)

⭐ Summary

A cloud-based compiler that executes Python and Java programs on AWS EC2, securely stores successful source files in Amazon S3, and integrates GitHub, CodeBuild, and CodePipeline for automated CI/CD.

📈Project ScreenShots
if code successfully executes in compiler


![alt text](image.png)


![alt text](image-1.png)


![alt text](image-2.png)


if code not exceuted


![alt text](image-3.png)


successfully executed code is stored in S3 bucket with proper file name and extensions


![alt text](image-4.png)


![alt text](image-5.png)
