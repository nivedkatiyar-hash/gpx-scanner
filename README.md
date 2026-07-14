# 🚀 gpx (Git Package eXecutor)

`gpx` is a lightweight, blazing-fast, and modular package manager for developers. It allows you to instantly download, manage, and execute Python scripts and tools directly from GitHub repositories without dealing with complex environments or bloated dependencies.

Built entirely with standard Python libraries—no external dependencies required.

---

## ✨ Core Features

- **Zero Dependencies:** Runs on standard Python 3. No `pip install`, no virtual environments needed.
- **Direct GitHub Integration:** Install any public tool directly using `gpx app install username/repo`.
- **Modular Ecosystem:** Expand `gpx` with powerful plugins for security, credential management, and productivity.
- **Verb-Noun CLI:** Intuitive command structure (e.g., `gpx app list`, `gpx plugin run`).

---

## 📦 Installation

To install `gpx` on your system, clone this repository and add it to your system path, or run the installer script:

```bash
git clone [https://github.com/YOUR-USERNAME/gpx.git](https://github.com/YOUR-USERNAME/gpx.git)
cd gpx
python3 install.py
-----------
GPX-scanner ( scans files for malware ) 
gpx plugin install YOUR-USERNAME/gpx-scan
gpx scan <app-name>
--------------------------------------------
🔒 gpx-vault (Offline Credential Manager)
Stop storing API keys in plain text. gpx-vault uses AES envelope encryption, master passwords, and recovery keys to secure your credentials locally.
Bash
gpx plugin install YOUR-USERNAME/gpx-vault
gpx vault setup
gpx vault add github user@email.com
-----------------------------------------------
💼 gpx-admin (Headless CRM & Invoicing)
A terminal-based time tracker and invoice generator for freelancers. Log hours instantly and generate professional status reports.
Bash
gpx plugin install YOUR-USERNAME/gpx-admin
gpx admin log "Acme Corp" 2.5 "Fixed database issues"
gpx admin invoice "Acme Corp" 75 --bill
