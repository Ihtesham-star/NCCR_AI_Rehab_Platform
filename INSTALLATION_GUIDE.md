# 📦 NCCR Rehabilitation Platform - Installation Guide

## 🎯 Quick Installation (3 Steps)

### Requirements:
- ✅ Windows PC/Laptop
- ✅ Python 3.9 or higher installed ([Download Python](https://www.python.org/downloads/))
- ✅ Internet connection (for first-time installation only)

---

## 📋 Installation Steps:

### Step 1: Install Python (if not already installed)
1. Download Python from: https://www.python.org/downloads/
2. **IMPORTANT:** During installation, check ☑️ "Add Python to PATH"
3. Click "Install Now"

### Step 2: Copy Workspace Folder
- Copy the entire workspace folder to your desired location
- Example: `C:\NCCR_Software\`

### Step 3: Run Installation Script
1. Open the workspace folder
2. **Right-click** `INSTALL.ps1`
3. Select **"Run with PowerShell"**
4. Wait 2-3 minutes for installation to complete
5. Press any key when you see "✓ Installation Complete!"

---

## ⚠️ If PowerShell Script is Blocked:

If you see a security error when running `INSTALL.ps1`:

**Solution:**
1. Right-click **Start Menu** → Select **"Windows PowerShell (Admin)"**
2. Run this command:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```
3. Type `Y` and press Enter
4. Close PowerShell
5. Try running `INSTALL.ps1` again

---

## 🚀 Starting the Software:

After installation is complete:

1. **Double-click** `START_SYSTEM.vbs`
2. Wait 10-15 seconds
3. Browser will automatically open
4. Start using the platform!

---

## 🔴 Stopping the Software:

**Option 1 (Recommended):**
- Click the **🔴 Shutdown System** button in the sidebar


---

## 📊 Database Options:

### Fresh Installation (No existing data):
- `INSTALL.ps1` automatically creates a new empty database
- Import your data through the **📤 Import Data** page

### Transfer with Existing Data:
- Make sure `nccr_rehabilitation.db` file is included when copying workspace
- `INSTALL.ps1` will detect it and keep your existing data safe
- No need to import data again - everything is already there!

---

## 🆘 Troubleshooting:

### "Python is not installed" error:
- Install Python from python.org
- Make sure "Add Python to PATH" was checked during installation
- Restart your computer after Python installation

### "Failed to install dependencies" error:
- Check your internet connection
- Try running `INSTALL.ps1` again
- If issue persists, manually run:
  ```powershell
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### Software doesn't start:
- Make sure installation completed successfully
- Check if Python processes are already running (Task Manager)
- Close any existing Python processes and try again

---

## 📞 Support:

For technical support, contact your system administrator or refer to the user manual.

---

**System Requirements:**
- OS: Windows 10/11
- RAM: 4GB minimum (8GB recommended)
- Storage: 2GB free space
- Python: 3.9 or higher
- Internet: Required for installation only (software works offline after installation)

---

**Installation Time:** 2-5 minutes (depending on internet speed)

**Made for:** National Center for Children's Rehabilitation (NCCR)
