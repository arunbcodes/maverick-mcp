# Rancher Desktop Setup Guide

Complete guide for running Maverick MCP with Rancher Desktop.

## Why Rancher Desktop?

**Rancher Desktop** is a free, open-source alternative to Docker Desktop with several advantages:

### Advantages

| Feature | Rancher Desktop | Docker Desktop |
|---------|----------------|----------------|
| **License** | Apache 2.0 (Free & Open Source) | Freemium (Paid for business >250 employees) |
| **Resource Usage** | Generally lighter (800MB-1.5GB RAM) | Heavier (2GB+ RAM) |
| **Kubernetes** | Built-in K3s (production-grade) | Built-in (resource intensive) |
| **Container Runtime** | Choose: containerd or dockerd | dockerd only |
| **CLI Tools** | Includes kubectl, helm, nerdctl | Docker CLI only |
| **Updates** | Monthly releases, community-driven | Commercial release cycle |
| **Privacy** | No telemetry or tracking | Analytics enabled by default |

### When to Use Rancher Desktop

✅ **Perfect for:**
- macOS users (especially Apple Silicon M1/M2/M3)
- Linux users wanting lightweight Kubernetes
- Open source advocates
- Development environments
- Learning Kubernetes
- Organizations avoiding Docker licensing fees

⚠️ **Consider Docker Desktop if:**
- You need Docker Extensions marketplace
- Your team is already standardized on Docker Desktop
- You require Docker Desktop Business features

## Installation

### macOS

**1. Download Rancher Desktop**
```bash
# Method 1: Direct download
open https://rancherdesktop.io/

# Method 2: Homebrew (recommended)
brew install --cask rancher
```

**2. Install and Launch**
```bash
# Open Rancher Desktop application
open -a "Rancher Desktop"
```

**3. First-Time Setup Wizard**

When you first launch Rancher Desktop, you'll see the setup wizard:

**Step 1: Enable Kubernetes (Optional)**
```
☑ Enable Kubernetes
Version: v1.28.x (stable)
```
- For Maverick MCP only: You can **disable** Kubernetes to save resources
- For future K8s deployment: **Enable** it

**Step 2: Container Runtime**
```
● dockerd (moby) - Recommended for Docker compatibility
○ containerd (nerdctl) - For Kubernetes-native workflows
```
- **Choose dockerd** for full Docker compatibility with Maverick MCP

**Step 3: Path Configuration**
```
☑ Automatic
```
- Adds Docker CLI to your PATH automatically

### Linux (Ubuntu/Debian)

**Install from package:**
```bash
# Download latest .deb package
curl -s https://api.github.com/repos/rancher-sandbox/rancher-desktop/releases/latest \
  | grep "browser_download_url.*amd64.deb" \
  | cut -d : -f 2,3 \
  | tr -d \" \
  | wget -i -

# Install
sudo dpkg -i rancher-desktop-*.deb

# Fix dependencies if needed
sudo apt-get install -f
```

**Launch:**
```bash
rancher-desktop
```

### Windows

**1. Download Installer**
- Visit [https://rancherdesktop.io/](https://rancherdesktop.io/)
- Download Windows installer (.exe)

**2. Install**
- Run installer as Administrator
- Choose installation directory
- Complete setup wizard (same as macOS)

**3. Configure WSL2**
```powershell
# Ensure WSL2 is enabled
wsl --install
wsl --set-default-version 2
```

## Configuration

### Recommended Settings

**1. Open Rancher Desktop Preferences**
- macOS: Rancher Desktop → Preferences
- Linux: File → Preferences
- Windows: Settings icon

**2. Container Engine**
```
Container Engine: dockerd (moby)
```
✅ **This is critical** - Ensures full Docker compatibility

**3. Kubernetes (Optional)**

**For Docker-only usage (Recommended for Maverick MCP):**
```
☐ Enable Kubernetes
```
- Saves ~1GB RAM
- Faster startup
- Simpler setup

**For future K8s deployment:**
```
☑ Enable Kubernetes
Kubernetes Version: v1.28.x (latest stable)
Container Runtime: dockerd
```

**4. Resources**

Allocate resources based on your system:

**Minimum (Development):**
```
CPUs: 2
Memory: 4GB
Disk: 20GB
```

**Recommended (Production-like):**
```
CPUs: 4
Memory: 8GB
Disk: 50GB
```

**For Apple Silicon Macs:**
```
CPUs: 4-6 (M1/M2/M3 are efficient)
Memory: 8GB
Disk: 50GB
```

**5. Virtual Machine**

**macOS:**
```
Type: VZ (Virtualization.framework)
```
- Faster than QEMU
- Native Apple Silicon support
- Better integration

**Linux:**
```
Type: None (runs natively)
```

**Windows:**
```
Type: WSL2
Distribution: Ubuntu 22.04 LTS
```

### Docker Socket Configuration

Rancher Desktop uses a different socket path than Docker Desktop.

**Check your socket location:**
```bash
# macOS/Linux
echo $DOCKER_HOST

# Should show:
# unix:///Users/YOUR_USERNAME/.rd/docker.sock  (macOS)
# unix:///var/run/docker.sock                  (Linux)
```

**If not set (macOS only):**
```bash
# Add to ~/.zshrc or ~/.bashrc
export DOCKER_HOST="unix://$HOME/.rd/docker.sock"

# Reload shell
source ~/.zshrc
```

**Test Docker connection:**
```bash
docker info
# Should show Rancher Desktop details
```

## Running Maverick MCP

### Quick Start

**1. Verify Rancher Desktop is Running**
```bash
# Check Docker is available
docker ps
# Should return empty list (no error)

# Check socket
ls -la ~/.rd/docker.sock  # macOS
# Should show socket file
```

**2. Clone and Configure**
```bash
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# Configure environment
cp .env.example .env
nano .env  # Add your TIINGO_API_KEY
```

**3. Start Services**
```bash
# Using Makefile
make docker-up

# Or direct docker-compose
docker-compose up --build -d
```

**4. Verify Services**
```bash
# Check containers
docker ps

# Check logs
docker-compose logs -f backend

# Test endpoint
curl http://localhost:8003/sse/
```

### Troubleshooting Rancher Desktop

#### Socket Not Found

**Problem:**
```bash
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
```bash
# macOS - Set DOCKER_HOST
export DOCKER_HOST="unix://$HOME/.rd/docker.sock"

# Add to shell profile permanently
echo 'export DOCKER_HOST="unix://$HOME/.rd/docker.sock"' >> ~/.zshrc
source ~/.zshrc
```

#### Container Fails to Start

**Problem:**
```
Error: Cannot start container
```

**Solutions:**
1. **Check Rancher Desktop is running:**
   ```bash
   # macOS
   pgrep -f "Rancher Desktop"
   ```

2. **Restart Rancher Desktop:**
   - Quit and relaunch application
   - Or: Rancher Desktop → Preferences → Reset Kubernetes

3. **Check resources:**
   - Preferences → Resources
   - Increase memory to 4GB minimum

#### Port Already in Use

**Problem:**
```
Error: Port 8003 already allocated
```

**Check what's using the port:**
```bash
# macOS/Linux
lsof -i :8003

# Kill process if needed
kill -9 <PID>
```

**Or change port in docker-compose.yml:**
```yaml
services:
  backend:
    ports:
      - "8004:8000"  # Changed from 8003
```

#### Volume Permission Errors

**Problem:**
```
Error: Permission denied accessing /app/maverick_mcp
```

**Solution:**
```bash
# Fix ownership (container runs as UID 1000)
sudo chown -R $(whoami):staff ./maverick_mcp

# macOS - Add to file sharing (if needed)
# Rancher Desktop → Preferences → Virtual Machine → Volumes
# Add: /Users/YOUR_USERNAME/path/to/maverick-mcp
```

#### Kubernetes Conflicts

**Problem:**
```
Error: Port 6443 already in use
```

**Solution:**
- Rancher Desktop → Preferences → Kubernetes
- Disable if not needed for Maverick MCP
- Or change Kubernetes port

## Performance Optimization

### Resource Tuning

**Check current resource usage:**
```bash
# Container stats
docker stats

# Rancher Desktop VM stats (macOS)
vm_stat | grep -i "Pages active"
```

**Optimize for Maverick MCP:**

1. **Disable Kubernetes** (if not needed):
   - Saves ~1GB RAM
   - Faster startup (10s vs 60s)
   - Simpler debugging

2. **Adjust VM Resources:**
   ```
   CPUs: 2-4 (sufficient for Maverick MCP)
   Memory: 4-6GB (8GB for comfortable use)
   ```

3. **Limit Container Resources:**
   Add to docker-compose.yml:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Disk Space Management

**Check disk usage:**
```bash
# Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes
```

**Rancher Desktop disk limits:**
- Preferences → Virtual Machine → Disk Size
- Default: 60GB (adjust as needed)

## CLI Tools Included

Rancher Desktop includes several CLI tools:

### Docker CLI
```bash
docker --version
docker-compose --version
```

### Kubernetes Tools (if K8s enabled)
```bash
kubectl version
kubectl get nodes

helm version
```

### nerdctl (containerd CLI)
```bash
# If using containerd runtime
nerdctl version
nerdctl ps
```

### Rancher Desktop CLI
```bash
# Check RD status
rdctl --help

# List all VMs
rdctl list-settings

# Version info
rdctl version
```

## Kubernetes Integration (Optional)

If you enabled Kubernetes, you can deploy Maverick MCP to K8s:

### Quick K8s Deployment

**1. Check K8s is ready:**
```bash
kubectl cluster-info
kubectl get nodes
```

**2. Create namespace:**
```bash
kubectl create namespace maverick-mcp
```

**3. Deploy (basic):**
```bash
# Build and load image to K8s
docker-compose build
docker save maverick-mcp-backend:latest | kubectl load -n maverick-mcp

# Deploy
kubectl apply -f k8s/deployment.yaml  # If available
```

**See [Kubernetes Deployment Guide](kubernetes.md) for complete K8s setup** (coming in Phase 3).

## Comparison with Docker Desktop

### Feature Parity for Maverick MCP

| Feature | Rancher Desktop | Docker Desktop |
|---------|----------------|----------------|
| **Docker CLI** | ✅ Full compatibility | ✅ Native |
| **docker-compose** | ✅ Fully supported | ✅ Native |
| **Volume mounts** | ✅ Works perfectly | ✅ Works perfectly |
| **Port mapping** | ✅ Works perfectly | ✅ Works perfectly |
| **Image building** | ✅ BuildKit support | ✅ BuildKit support |
| **Networks** | ✅ Bridge, host, custom | ✅ Bridge, host, custom |
| **Performance** | ✅ Fast (VZ on macOS) | ✅ Fast |

### Migration from Docker Desktop

**Switching from Docker Desktop to Rancher Desktop:**

1. **Export images:**
   ```bash
   # While Docker Desktop is running
   docker save maverick-mcp-backend:latest > backend.tar
   ```

2. **Switch to Rancher Desktop:**
   - Quit Docker Desktop
   - Launch Rancher Desktop
   - Wait for startup

3. **Load images:**
   ```bash
   docker load < backend.tar
   ```

4. **Start services:**
   ```bash
   cd maverick-mcp
   docker-compose up -d
   ```

**No configuration changes needed!** Rancher Desktop is drop-in compatible.

## Best Practices

### Development Workflow

**1. Use Rancher Desktop for development:**
```bash
# Start Rancher Desktop when working
# Stop when not in use (saves battery on laptops)

# Quick start
docker-compose up -d

# Quick stop
docker-compose down
```

**2. Resource Management:**
```bash
# Monitor resources
docker stats

# Clean up regularly
docker system prune -f
```

**3. Shell Aliases:**
Add to ~/.zshrc or ~/.bashrc:
```bash
# Docker shortcuts
alias dps='docker ps'
alias dlog='docker-compose logs -f'
alias dup='docker-compose up -d'
alias ddown='docker-compose down'

# Maverick MCP shortcuts
alias mcp-start='cd ~/maverick-mcp && make docker-up'
alias mcp-stop='cd ~/maverick-mcp && make docker-down'
alias mcp-logs='cd ~/maverick-mcp && make docker-logs'
```

### macOS-Specific Tips

**1. VZ vs QEMU:**
- Always use **VZ** (Virtualization.framework)
- Native Apple Silicon support
- 2-3x faster than QEMU

**2. File Sharing:**
- Rancher Desktop → Preferences → Virtual Machine → Volumes
- Only share directories you need
- Default: Entire home directory (slower)
- Recommended: Project directory only

**3. Battery Optimization:**
- Quit Rancher Desktop when not coding
- Or disable Kubernetes to reduce CPU usage

## Updating Rancher Desktop

**Check for updates:**
```bash
# In app: Rancher Desktop → Check for Updates

# CLI
rdctl version
```

**Update process:**
1. Quit Rancher Desktop
2. Download latest version
3. Install (overwrites previous)
4. Restart Rancher Desktop

**After update:**
```bash
# Verify Docker still works
docker version

# Restart Maverick MCP if running
cd maverick-mcp
docker-compose restart
```

## Uninstalling

**macOS:**
```bash
# Quit Rancher Desktop first

# Method 1: Via Homebrew
brew uninstall --cask rancher

# Method 2: Manual
rm -rf ~/Applications/Rancher\ Desktop.app
rm -rf ~/.rd
rm -rf ~/.local/share/rancher-desktop

# Remove Docker socket link
rm ~/.docker/run/docker.sock
```

**Linux:**
```bash
# Ubuntu/Debian
sudo dpkg -r rancher-desktop

# Remove data
rm -rf ~/.local/share/rancher-desktop
rm -rf ~/.rd
```

**Windows:**
```powershell
# Uninstall via Settings → Apps
# Or run uninstaller from installation directory

# Remove data
Remove-Item -Recurse "$env:LOCALAPPDATA\rancher-desktop"
```

## Additional Resources

- [Rancher Desktop Official Docs](https://docs.rancherdesktop.io/)
- [GitHub Repository](https://github.com/rancher-sandbox/rancher-desktop)
- [Docker Deployment Guide](docker.md) - General Docker guide
- [Maverick MCP Documentation](https://arunbcodes.github.io/maverick-mcp/)

## Next Steps

- [ ] Install and configure Rancher Desktop
- [ ] Run Maverick MCP in containers
- [ ] Explore [Kubernetes deployment](kubernetes.md) (Phase 3)
- [ ] Set up [production environment](production.md) (Phase 2)
