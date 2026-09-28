---
Document ID: TROUBLESHOOTING-QUICKSTART
Title: "Quick Start Troubleshooting Guide"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Beginner
---

# Quick Start Troubleshooting Guide

**Common Issues & Solutions for Quick Start**

**Last Updated:** 2026-02-04
**Reading Time:** 5 minutes

---

## 🔍 Quick Diagnosis

### Find Your Issue Fast

| Symptom | Go To Section |
|---------|--------------|
| Ollama won't install | [Installation Issues](#-installation-issues) |
| Model download stuck/fails | [Download Problems](#-download-problems) |
| "Connection refused" error | [Connection Issues](#-connection-issues) |
| Out of memory errors | [Memory Issues](#-memory-issues) |
| Model runs very slow | [Performance Issues](#-performance-issues) |
| Ollama commands not found | [Command Not Found](#-command-not-found) |

---

## 📥 Installation Issues

### Issue: "Ollama not found" after installation

**Windows:**
1. Check if Ollama is in PATH:
   ```powershell
   where ollama
   ```

2. If not found, add to PATH:
   - Search "Environment Variables" in Windows
   - Edit PATH variable
   - Add: `C:\Users\[YourUser]\AppData\Local\Programs\Ollama`
   - Restart terminal

**Mac:**
```bash
# Check if Ollama is installed
which ollama

# If not found, reinstall
brew reinstall ollama
```

**Linux:**
```bash
# Check installation
which ollama

# If not found, reinstall
curl -fsSL https://ollama.com/install.sh | sh
```

---

### Issue: Installation fails halfway

**Symptoms:**
- Download stops at random percentage
- "Network error" or "Connection lost"

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping google.com
   ```

2. **Try alternative mirror (Linux):**
   ```bash
   export OLLAMA_HOST=https://ollama.com
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **Disable VPN/Proxy temporarily:**
   - VPNs can block installation
   - Disable and retry

4. **Windows - Download manually:**
   - Download installer from ollama.com
   - Run installer as Administrator

---

## ⬇️ Download Problems

### Issue: Model download stuck at 0%

**Symptoms:**
- `ollama pull mistral` hangs
- No progress for minutes

**Solutions:**

1. **Verify Ollama is running:**
   ```bash
   # Check if ollama process exists
   ps aux | grep ollama    # Mac/Linux
   tasklist | findstr ollama  # Windows
   ```

2. **Start Ollama server:**
   ```bash
   ollama serve
   ```

3. **In another terminal, pull model:**
   ```bash
   ollama pull mistral
   ```

4. **Check firewall:**
   - Windows: Allow Ollama through Windows Firewall
   - Mac: Allow in Security & Privacy
   - Linux: Check `ufw` or `iptables`

---

### Issue: Download very slow

**Symptoms:**
- Download progresses at <1MB/s
- Takes hours for 4GB model

**Solutions:**

1. **Check internet speed:**
   ```bash
   # Use browser speed test
   # Or: curl -o /dev/null http://speedtest.tele2.net/10MB.zip
   ```

2. **Try different time of day:**
   - Off-peak hours (early morning/late night)
   - Less network congestion

3. **Use smaller model first:**
   ```bash
   # Try 2GB model instead of 4GB
   ollama pull phi3
   ```

4. **Check if ISP throttling:**
   - Some ISPs limit large downloads
   - Contact ISP if issue persists

---

### Issue: "Out of disk space"

**Symptoms:**
- "No space left on device"
- Download fails near completion

**Solutions:**

1. **Check available space:**
   ```bash
   # Mac/Linux
   df -h

   # Windows
   wmic logicaldisk get size,freespace,caption
   ```

2. **Free up space:**
   - Delete temporary files
   - Empty trash/recycle bin
   - Remove old models:
     ```bash
     ollama list
     ollama rm [model-name]
     ```

3. **Change model storage location:**
   ```bash
   # Set environment variable
   export OLLAMA_MODELS=/path/to/large/drive/.ollama/models

   # Windows: Set in Environment Variables
   # Variable: OLLAMA_MODELS
   # Value: D:\.ollama\models
   ```

---

## 🔌 Connection Issues

### Issue: "Connection refused" when running ollama

**Symptoms:**
- `ollama run mistral` fails
- Error: "connection refused" or "dial tcp: lookup ollama.com"

**Solutions:**

1. **Check if Ollama server is running:**
   ```bash
   # Windows: Check Task Manager for "ollama app"
   # Mac/Linux:
   ps aux | grep ollama
   ```

2. **Start Ollama server:**
   ```bash
   ollama serve
   ```

3. **Check port 11434 (Ollama's default port):**
   ```bash
   # Check if port is in use
   netstat -an | grep 11434  # Mac/Linux
   netstat -an | findstr 11434  # Windows
   ```

4. **Verify no firewall blocking:**
   - Windows: Allow Ollama through Windows Firewall
   - Mac: System Preferences → Security & Privacy → Firewall
   - Linux: `sudo ufw allow 11434`

---

### Issue: WSL2 network problems (Windows)

**Symptoms:**
- WSL2 can't access internet
- Ollama works in Windows but not WSL2

**Solutions:**

1. **Restart WSL2:**
   ```powershell
   wsl --shutdown
   wsl
   ```

2. **Check WSL2 network:**
   ```bash
   # In WSL2
   ping google.com
   cat /etc/resolv.conf
   ```

3. **Reset WSL2 network:**
   ```powershell
   # In PowerShell (Admin)
   wsl --shutdown
   # Delete .wslconfig if exists
   # Restart WSL2
   ```

4. **Use Ollama from Windows PowerShell:**
   - Ollama works fine in Windows
   - Use PowerShell instead of WSL2

---

## 💾 Memory Issues

### Issue: "Out of memory" error

**Symptoms:**
- "Cannot allocate memory"
- Model fails to load
- System becomes unresponsive

**Solutions:**

1. **Check available RAM:**
   ```bash
   # Mac/Linux
   free -h

   # Windows
   systeminfo | findstr "Available Physical Memory"
   ```

2. **Use smaller model:**
   ```bash
   # Instead of mistral (7B)
   ollama pull phi3      # 3.8B parameters
   ollama pull gemma:2b  # 2B parameters
   ```

3. **Close other applications:**
   - Free up RAM by closing browser, other apps
   - Check Task Manager / Activity Monitor

4. **Adjust Ollama memory settings:**
   ```bash
   # Set maximum memory (in GB)
   ollama run mistral --num-gpu 0  # Force CPU mode

   # Limit context length (less memory)
   ollama run mistral --ctx-size 512  # Instead of default 2048
   ```

---

### Issue: GPU out of memory (VRAM)

**Symptoms:**
- "CUDA out of memory"
- Model loads but fails on inference

**Solutions:**

1. **Check GPU memory:**
   ```bash
   nvidia-smi
   ```

2. **Use CPU mode:**
   ```bash
   ollama run mistral --num-gpu 0
   ```

3. **Use quantized model:**
   ```bash
   # 4-bit quantization uses less VRAM
   ollama pull mistral:7b-q4_0
   ```

4. **Reduce context size:**
   ```bash
   ollama run mistral --ctx-size 1024
   ```

---

## ⚡ Performance Issues

### Issue: Model very slow on CPU

**Symptoms:**
- Takes >30 seconds for each response
- 100% CPU usage

**Solutions:**

1. **Use smaller/faster model:**
   ```bash
   ollama pull phi3
   ollama run phi3 "test"
   ```

2. **Reduce context length:**
   ```bash
   ollama run phi3 --ctx-size 512
   ```

3. **Use quantized model:**
   ```bash
   ollama pull mistral:7b-q4_0
   ```

4. **Accept slower performance:**
   - CPU mode is 10-20x slower than GPU
   - Still usable for learning

---

### Issue: First response very slow

**Symptoms:**
- First prompt takes >1 minute
- Subsequent prompts faster

**Explanation:**
- First load requires reading model from disk
- Model stays in RAM after first load

**Solution:**
- This is normal behavior
- Model loads faster on subsequent runs

---

## ❓ Command Not Found

### Issue: 'ollama' command not found

**Symptoms:**
- `bash: ollama: command not found`
- Command doesn't autocomplete

**Solutions:**

1. **Check installation:**
   ```bash
   which ollama  # Mac/Linux
   where ollama  # Windows
   ```

2. **Reinstall Ollama:**
   - Mac: `brew reinstall ollama`
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows: Re-run installer

3. **Add to PATH (if not already):**
   - Mac/Linux: Add `export PATH="$PATH:/usr/local/bin"`
   - Windows: Add Ollama path to Environment Variables

4. **Restart terminal:**
   - Close and reopen terminal
   - Or run: `source ~/.bashrc` or `source ~/.zshrc`

---

## 🆘 Still Stuck?

### Complete Reset

If nothing works, perform complete reset:

**1. Uninstall Ollama completely:**

**Mac:**
```bash
brew uninstall ollama
rm -rf ~/.ollama
```

**Linux:**
```bash
rm -rf /usr/local/bin/ollama
rm -rf ~/.ollama
```

**Windows:**
- Uninstall via Apps & Features
- Delete `%USERPROFILE%\.ollama`

**2. Reinstall:**
- Follow [QUICK-START.md](QUICK-START.md) from scratch

**3. Test with smallest model:**
```bash
ollama pull phi3
ollama run phi3 "test"
```

---

## 📞 Get Help

### Additional Resources

1. **Official Ollama Docs:** https://ollama.com/docs
2. **Ollama GitHub Issues:** https://github.com/ollama/ollama/issues
3. **PROJECT-OMEGA Setup Guide:** [ENVIRONMENT-SETUP.md](ENVIRONMENT-SETUP.md)
4. **Environment Lab:** [LAB-000-ENVIRONMENT-SETUP.md](../learning-resources/labs/LAB-000-ENVIRONMENT-SETUP.md)

### Common Error Messages

| Error | Most Likely Cause | Solution |
|-------|-------------------|----------|
| "command not found" | Not in PATH | Reinstall or add to PATH |
| "connection refused" | Ollama not running | Run `ollama serve` |
| "out of memory" | Insufficient RAM | Use smaller model |
| "no space left" | Disk full | Free up space |
| "network unreachable" | No internet | Check connection |

---

## ✅ Verification Checklist

After troubleshooting, verify:

- [ ] `ollama --version` works
- [ ] `ollama serve` starts without errors
- [ ] `ollama list` shows installed models
- [ ] `ollama run phi3 "test"` generates response

**All checks pass?** You're ready! Continue with [TUTORIAL-001-Hello-LLM.md](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)

---

**Still having issues?** Join our community or check the [complete setup guide](ENVIRONMENT-SETUP.md).

