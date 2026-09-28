---
Document ID: CHEAT-SHEET-004
Title: "CHEAT SHEET: Linux Commands for AI/ML"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# CHEAT SHEET: Linux Commands for AI/ML

**Essential Linux commands for AI/ML development**

---

## 📁 File & Directory Operations

### Navigation
```bash
# Change directory
cd /path/to/directory
cd ~                    # Home directory
cd ..                   # Parent directory
cd -                    # Previous directory

# Print working directory
pwd

# List files
ls                      # Basic list
ls -la                  # Detailed list with hidden files
ls -lh                  # Human-readable sizes
ls -lt                  # Sort by time (newest first)
ls -lhS                 # Sort by size (largest first)

# Tree view
tree                    # Directory tree
tree -L 2               # Depth 2
tree -d                 # Directories only
```

### File Operations
```bash
# Create file
touch file.txt
echo "content" > file.txt

# Copy files
cp file.txt copy.txt
cp -r directory/ new_directory/
cp -p file.txt backup.txt    # Preserve permissions

# Move/Rename
mv old.txt new.txt
mv file.txt directory/

# Remove files
rm file.txt
rm -rf directory/            # Recursive force (DANGER!)

# Find files
find . -name "*.py"          # Find Python files
find . -type f -mtime -7     # Modified in last 7 days
find . -size +100M           # Larger than 100MB
find . -empty                # Empty files/directories
```

### Directory Operations
```bash
# Create directory
mkdir new_dir
mkdir -p path/to/nested/dir  # Create parents

# Remove directory
rmdir empty_dir
rm -r directory/

# Disk usage
du -sh directory/            # Size of directory
du -sh * | sort -h           # Size of all items, sorted
df -h                        # Disk space free
```

---

## 👀 Viewing Files

### File Content
```bash
# View entire file
cat file.txt

# View with line numbers
cat -n file.txt

# View first lines
head file.txt                # First 10 lines
head -n 20 file.txt          # First 20 lines

# View last lines
tail file.txt                # Last 10 lines
tail -f log.txt              # Follow (watch file grow)
tail -n 50 file.txt          # Last 50 lines

# View specific lines
sed -n '10,20p' file.txt     # Lines 10-20

# Search in file
grep "pattern" file.txt
grep -r "pattern" directory/  # Recursive search
grep -i "pattern" file.txt    # Case insensitive
grep -v "pattern" file.txt    # Invert match
grep -n "pattern" file.txt    # Show line numbers
```

### File Info
```bash
# File type
file model.safetensors

# File size
ls -lh file.txt
wc -c file.txt               # Bytes
wc -l file.txt               # Lines
wc -w file.txt               # Words

# Detailed info
stat file.txt
```

---

## 📝 Text Processing

### Editing Files
```bash
# Nano editor
nano file.txt

# Vim editor
vim file.txt
# :w - save, :q - quit, :wq - save & quit

# Create file with content
cat > file.txt << EOF
Line 1
Line 2
EOF

# Append to file
echo "new line" >> file.txt
```

### Text Manipulation
```bash
# Sort
sort file.txt
sort -n file.txt             # Numeric sort
sort -r file.txt             # Reverse
sort -u file.txt             # Unique lines

# Remove duplicates
uniq file.txt
sort file.txt | uniq         # Sort first, then unique

# Count occurrences
sort file.txt | uniq -c
sort file.txt | uniq -c | sort -rn  # By frequency

# Replace text
sed 's/old/new/g' file.txt
sed -i 's/old/new/g' file.txt  # Edit in place

# Extract columns
awk '{print $1, $3}' file.txt   # Columns 1 and 3
cut -d',' -f1 file.txt          # Field 1 (comma delimiter)
```

### Advanced Processing
```bash
# Chain commands
cat file.txt | grep "pattern" | sort | uniq -c

# Count files by extension
find . -type f | sed 's/.*\.//' | sort | uniq -c

# Find largest files
find . -type f -exec du -h {} + | sort -rh | head -10

# Batch rename
rename 's/old/new/' *.txt

# Remove empty lines
grep . file.txt > clean.txt
```

---

## 🔍 Process Management

### View Processes
```bash
# List all processes
ps aux

# Interactive process viewer
top
htop                        # Better version

# Find specific process
ps aux | grep python
pgrep python                # PID only
pidof python                # PID of command
```

### Control Processes
```bash
# Stop process (Ctrl+C in terminal)
kill ${PID}
kill -9 ${PID}              # Force kill

# Stop by name
pkill python
killall python

# Run in background
command &

# Bring to background: Ctrl+Z, then:
bg                           # Resume in background
fg                           # Bring to foreground

# Detach from terminal
nohup command > output.log 2>&1 &

# Run with lower priority
nice -n 19 command          # Lowest priority
renice -n 5 -p ${PID}        # Change priority
```

### GPU Processes
```bash
# View GPU usage
nvidia-smi

# Watch GPU usage
watch -n 1 nvidia-smi

# GPU processes
nvidia-smi pmon

# Detailed GPU info
nvidia-smi qmon

# Kill process on specific GPU
fuser -v /dev/nvidiaX       # Find processes
kill ${PID}                  # Kill process
```

---

## 🌐 Network Commands

### Network Info
```bash
# IP address
ip addr
ifconfig                    # Older command

# Network connections
netstat -tuln               # TCP/UDP listening
ss -tuln                    # Modern alternative

# Test connectivity
ping google.com
ping -c 4 host              # Count

# Port check
netstat -tulpn | grep :8000
lsof -i :8000               # Who's using port 8000

# Bandwidth
iftop                       # Live bandwidth
nethogs                     # Per-process bandwidth
```

### Transfer Files
```bash
# Download file
wget https://example.com/file.zip
curl -O https://example.com/file.zip

# SCP (secure copy)
scp file.txt user@host:/path/
scp user@host:/path/file.txt ./

# SCP with port
scp -P 2222 file.txt user@host:/path/

# Rsync (sync directories)
rsync -avz source/ destination/
rsync -avz -e ssh source/ user@host:destination/

# Progress bar for copy
pv file.txt > copy.txt
```

### SSH
```bash
# Connect
ssh user@host
ssh -p 2222 user@host       # Custom port

# SSH with key
ssh -i key.pem user@host

# SSH tunnel
ssh -L 8080:localhost:8080 user@host

# Execute command remotely
ssh user@host "command"

# Copy SSH key
ssh-copy-id user@host
```

---

## 🔒 Permissions

### View Permissions
```bash
# File permissions
ls -l file.txt

# Permission format: -rwxrwxrwx
# First char: - (file), d (directory), l (link)
# Next 3: Owner permissions (rwx)
# Next 3: Group permissions (rwx)
# Last 3: Others permissions (rwx)

# Detailed info
stat file.txt
```

### Change Permissions
```bash
# Symbolic mode
chmod +x script.sh          # Make executable
chmod -w file.txt            # Remove write
chmod u+x file.txt           # User execute
chmod g+r file.txt           # Group read
chmod o-w file.txt           # Others write

# Numeric mode
chmod 755 file.txt           # rwxr-xr-x
chmod 644 file.txt           # rw-r--r--
chmod 777 file.txt           # rwxrwxrwx (all permissions)

# Recursive
chmod -R 755 directory/
```

### Ownership
```bash
# Change owner
chown user file.txt
chown user:group file.txt

# Recursive
chown -R user:group directory/

# Change group only
chgrp group file.txt
```

---

## 💾 Disk & Memory

### Disk Usage
```bash
# Free space
df -h                        # Human-readable
df -i                        # Inodes

# Directory size
du -sh directory/
du -sh * | sort -h

# Largest directories
du -h --max-depth=1 | sort -rh | head -10

# Clean up
rm -rf /tmp/*               # Clear temp
sudo apt-get clean          # Clean apt cache
```

### Memory
```bash
# Memory usage
free -h                     # Human-readable
free -m                     # MB
free -g                     # GB

# Swap
swapon -s                   # Swap usage
dd if=/dev/zero of=/swapfile bs=1G count=4    # Create swap
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### GPU Memory
```bash
# GPU memory usage
nvidia-smi

# Clear GPU memory
# Kill process using GPU
nvidia-smi --gpu-reset       # Not always available
```

Python (clear CUDA cache):
```python
import torch
torch.cuda.empty_cache()
```

---

## 🔧 System Management

### Package Management (Ubuntu/Debian)
```bash
# Update packages
sudo apt update
sudo apt upgrade

# Install package
sudo apt install package-name

# Remove package
sudo apt remove package-name
sudo apt purge package-name   # Remove with config

# Search package
apt search keyword

# Show package info
apt show package-name
```

### Systemd Services
```bash
# Start service
sudo systemctl start service-name

# Stop service
sudo systemctl stop service-name

# Restart service
sudo systemctl restart service-name

# Enable on boot
sudo systemctl enable service-name

# Check status
sudo systemctl status service-name

# View logs
sudo journalctl -u service-name
sudo journalctl -u service-name -f  # Follow
```

### Docker Service
```bash
# Start Docker
sudo systemctl start docker

# Docker status
sudo systemctl status docker

# View Docker logs
sudo journalctl -u docker

# Restart Docker
sudo systemctl restart docker
```

---

## 📊 Monitoring

### System Monitoring
```bash
# Real-time monitoring
htop                        # CPU, memory, processes
iotop                       # I/O monitoring
nethogs                     # Network by process

# One-time stats
vmstat 1                    # Every second
iostat 1                    # I/O stats
mpstat 1                    # CPU stats

# GPU monitoring
nvidia-smi dmon             # Continuous
nvidia-smi pmon             # Per-process
```

### Logs
```bash
# View logs
journalctl                  # All logs
journalctl -xe              # Errors from this boot
journalctl -f               # Follow logs

# Application logs
tail -f /var/log/app.log
tail -n 100 /var/log/app.log

# Docker logs
docker logs container-name
docker logs -f container-name

# System logs
dmesg                       # Kernel messages
/var/log/syslog             # System log
```

---

## 🎯 AI/ML Specific

### Python Environment
```bash
# Create virtual environment
python -m venv venv
python -m venv .venv

# Activate
source venv/bin/activate      # Linux/Mac
source .venv/bin/activate

# Deactivate
deactivate

# Install packages
uv pip install -r requirements.txt
uv pip install torch torchvision
```

### Model Management
```bash
# Download models
wget https://huggingface.co/model/file.bin
huggingface-cli download model-name

# Model checkpoints
ls -lh checkpoints/
du -sh checkpoints/

# Move models
mv model.pt /models/
cp -r models/ /backup/models_$(date +%Y%m%d)/
```

### Data Management
```bash
# Dataset directory
mkdir -p data/{raw,processed,train,val,test}

# Check dataset size
du -sh data/
ls -lh data/train/*.jpg | wc -l

# Sample data
head -n 100 data/train.csv > data/train_sample.csv

# Split files
split -l 10000 large_file.txt chunk_

# Compress data
tar -czf data.tar.gz data/
zip -r data.zip data/

# Extract
tar -xzf data.tar.gz
unzip data.zip
```

---

## 🚀 Performance

### Parallel Processing
```bash
# Run in parallel
command1 & command2 & command3 &

# Wait for all
wait

# Parallel with xargs
find . -name "*.py" | xargs -P 4 python script.py

# GNU Parallel
parallel python script.py ::: file1 file2 file3
```

### Background Jobs
```bash
# Screen (persistent sessions)
screen -S session-name
# Ctrl+A, D to detach
screen -r session-name       # Reattach

# Tmux alternative
tmux new -s session-name
# Ctrl+B, D to detach
tmux attach -t session-name

# Nohup (run after logout)
nohup python train.py > train.log 2>&1 &
```

---

## 🔍 Troubleshooting

### System Issues
```bash
# Check logs
dmesg | tail
journalctl -xe

# Check resources
free -h
df -h
uptime

# Process issues
top
htop
ps aux --sort=-%mem | head -10

# Disk issues
df -i                        # Check inodes
sudo lsof | grep deleted     # Open deleted files
```

### Network Issues
```bash
# Check connection
ping -c 4 8.8.8.8

# Check DNS
nslookup google.com
dig google.com

# Check port
telnet host port
nc -zv host port

# Trace route
traceroute google.com
mtr google.com                # Better version
```

---

## 📝 Aliases & Functions

### Useful Aliases
```bash
# Add to ~/.bashrc
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'

# Docker aliases
alias dps='docker ps'
alias di='docker images'
alias dex='docker exec -it'

# Apply changes
source ~/.bashrc
```

### Useful Functions
```bash
# Extract function
extract() {
    if [ -f $1 ]; then
        case $1 in
            *.tar.bz2) tar xjf $1 ;;
            *.tar.gz) tar xzf $1 ;;
            *.bz2) bunzip2 $1 ;;
            *.rar) unrar x $1 ;;
            *.gz) gunzip $1 ;;
            *.tar) tar xf $1 ;;
            *.tbz2) tar xjf $1 ;;
            *.tgz) tar xzf $1 ;;
            *.zip) unzip $1 ;;
            *.Z) uncompress $1 ;;
            *.7z) 7z x $1 ;;
            *) echo "'$1' cannot be extracted" ;;
        esac
    fi
}

# Use: extract file.tar.gz

# Backup function
backup() {
    cp -r "$1" "$1.backup-$(date +%Y%m%d-%H%M%S)"
}

# Use: backup important_file.txt
```

---

## 🔗 Quick Links

- **[Tutorial 002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker basics
- **[CHEAT SHEET 001: Docker](CHEAT-SHEET-001-Docker.md)** - Docker commands
- **[CHEAT SHEET 002: Python AI](CHEAT-SHEET-002-Python-AI.md)** - Python for AI/ML
- **[LAB-001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Hands-on Docker practice

---

**Need more?** Check [TLDP](https://tldp.org/) or [Linux Journey](https://linuxjourney.com/)
