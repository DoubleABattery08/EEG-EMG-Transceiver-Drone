# SSH Setup for Raspberry Pi Access

You're getting "Permission denied (publickey)" because your Raspberry Pi only accepts SSH key authentication.

---

## Option 1: Enable Password Authentication (Quickest)

### Requirements:
- Physical access to Raspberry Pi (monitor + keyboard)
- OR existing SSH access from another device

### Steps on Raspberry Pi:

1. **Connect monitor and keyboard to Raspberry Pi**

2. **Login directly** (username: `drone`, password: your Pi password)

3. **Edit SSH configuration:**
```bash
sudo nano /etc/ssh/sshd_config
```

4. **Find and modify these lines:**
```
# Change from 'no' to 'yes':
PasswordAuthentication yes
PubkeyAuthentication yes

# Make sure this is also set:
PermitRootLogin no
```

5. **Save and exit:**
   - Press `Ctrl+X`
   - Press `Y`
   - Press `Enter`

6. **Restart SSH service:**
```bash
sudo systemctl restart sshd
```

7. **From Windows, try connecting:**
```powershell
ssh drone@drone.local
# Enter password when prompted
```

---

## Option 2: Use SSH Keys (More Secure)

### On Windows (PowerShell):

1. **Generate SSH key pair:**
```powershell
ssh-keygen -t ed25519 -C "drone-access"
```

When prompted:
- **File location:** Press `Enter` (use default: `C:\Users\Aaron\.ssh\id_ed25519`)
- **Passphrase:** Press `Enter` for no passphrase, OR enter a passphrase for extra security

2. **View your public key:**
```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519 ...`)

### On Raspberry Pi (physical access):

1. **Login to Pi with monitor/keyboard**

2. **Create .ssh directory (if it doesn't exist):**
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

3. **Add your public key:**
```bash
nano ~/.ssh/authorized_keys
```

4. **Paste the public key** you copied from Windows

5. **Save and exit:**
   - Press `Ctrl+X`
   - Press `Y`
   - Press `Enter`

6. **Set correct permissions:**
```bash
chmod 600 ~/.ssh/authorized_keys
```

### Back on Windows:

Try connecting:
```powershell
ssh drone@drone.local
```

Should connect without password!

---

## Option 3: USB/SD Card Method (No Monitor Needed)

If you don't have a monitor but can access the SD card:

1. **Shutdown Raspberry Pi**

2. **Remove SD card and insert into your Windows PC**

3. **Navigate to the boot partition** (should auto-mount)

4. **Create/edit SSH config:**
   - If there's a file called `userconf.txt` or `userconf`, you can set username/password there
   - For Raspberry Pi OS Bullseye or newer

5. **On Windows, generate password hash:**
```powershell
# Install openssl for Windows if you don't have it
# Or use online tool: https://www.browserling.com/tools/bcrypt

# You'll need the password hash for the Pi
```

6. **Create userconf.txt on boot partition:**
```
drone:$6$rounds=656000$YourHashedPasswordHere
```

7. **Re-insert SD card and boot Pi**

---

## Option 4: Default Credentials (If Pi was just set up)

Try these common defaults:

### Raspberry Pi OS (Bullseye/newer):
```powershell
ssh pi@drone.local
# Password: raspberry (if not changed)
```

### If username is 'drone':
```powershell
ssh drone@drone.local
# Try common passwords:
# - raspberry
# - drone
# - admin
# - (blank)
```

---

## Troubleshooting

### Issue: "Could not resolve hostname drone.local"

**Cause:** Windows can't find the Raspberry Pi on the network

**Solutions:**

1. **Install Bonjour/mDNS support on Windows:**
   - Download and install [Bonjour Print Services](https://support.apple.com/kb/DL999)
   - OR use IP address instead

2. **Find Pi's IP address:**

   **From your router:**
   - Log into your router admin page
   - Look for connected devices
   - Find "drone" or "raspberrypi"

   **From Windows (scan network):**
   ```powershell
   # Install nmap from https://nmap.org/download.html
   # Then scan your network:
   nmap -sn 192.168.1.0/24
   # Replace 192.168.1.0 with your network range
   ```

3. **Connect using IP address:**
```powershell
ssh drone@192.168.1.XXX
```

### Issue: Still "Permission denied" after enabling password auth

**Check SSH service status on Pi:**
```bash
sudo systemctl status ssh
```

**Check SSH config syntax:**
```bash
sudo sshd -t
```

**View SSH logs:**
```bash
sudo tail -f /var/log/auth.log
# Keep this running while you try to connect from Windows
```

### Issue: Wrong permissions on authorized_keys

**On Raspberry Pi:**
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## Quick Diagnostic Commands

### On Raspberry Pi:

```bash
# Check SSH service
sudo systemctl status ssh

# View SSH configuration
sudo cat /etc/ssh/sshd_config | grep -E "PasswordAuthentication|PubkeyAuthentication"

# Check authorized keys
ls -la ~/.ssh/authorized_keys

# Test SSH locally
ssh localhost
```

### On Windows:

```bash
# Check if key exists
dir $env:USERPROFILE\.ssh

# Verbose SSH connection (shows detailed error)
ssh -v drone@drone.local

# Test with password (force password auth)
ssh -o PreferredAuthentications=password drone@drone.local

# Test with key (force key auth)
ssh -o PreferredAuthentications=publickey drone@drone.local
```

---

## After You Connect Successfully

Once you're in via SSH, you can run the MindWave/Tello setup:

```bash
# Update system
sudo apt-get update

# Install dependencies
sudo apt-get install -y bluetooth bluez bluez-tools rfcomm python3-pip

# Clone or copy your project files to Pi
# Then follow RASPBERRY_PI_SETUP.md
```

---

## What's Your Current Situation?

**Choose the best option:**

- ✅ **Have monitor/keyboard?** → Use Option 1 (enable password auth)
- ✅ **Want most secure?** → Use Option 2 (SSH keys)
- ✅ **No monitor, can remove SD card?** → Use Option 3 (SD card method)
- ✅ **Fresh Pi install?** → Try Option 4 (default credentials)

**Need to find Pi's IP address?** → Check your router or use network scanner

---

## My Recommendation

**Easiest path:**
1. Connect monitor/keyboard to Raspberry Pi
2. Login directly as `drone`
3. Run: `sudo nano /etc/ssh/sshd_config`
4. Change `PasswordAuthentication no` to `PasswordAuthentication yes`
5. Run: `sudo systemctl restart sshd`
6. From Windows: `ssh drone@drone.local` (enter password)

Then proceed with MindWave/Tello setup!
