# NVIDIA GPU Docker Runtime Troubleshooting Guide

## Current Status

### ✅ Working: KataGo CPU Version
- **Container**: `katago-cpu` is running successfully
- **Performance**: Functional but slower than GPU version
- **Testing**: Verified with `test_katago.py` and `windows_test.py`

### ❌ Issue: KataGo GPU Version
- **Container**: `katago-gpu` fails to start
- **Error**: NVIDIA Docker runtime mount conflict
- **Specific Error**: `nvidia-container-cli: mount error: file creation failed: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1: file exists`

## Root Cause Analysis

The error indicates a conflict in NVIDIA Docker runtime where:
1. NVIDIA Container CLI is trying to mount GPU libraries
2. The target file `/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1` already exists
3. This creates a mount conflict preventing container startup

## Solutions (Try in Order)

### Solution 1: Restart Docker Desktop
```powershell
# Stop Docker Desktop completely
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

# Wait a few seconds, then restart Docker Desktop
# Or restart through Docker Desktop GUI
```

### Solution 2: Clean Docker System
```powershell
# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f
```

### Solution 3: Rebuild GPU Image
```powershell
# Remove existing GPU image
docker rmi katago-blackrice-katago-gpu -f

# Rebuild without cache
docker-compose build --no-cache katago-gpu

# Try starting again
docker-compose up -d katago-gpu
```

### Solution 4: Check NVIDIA Docker Runtime
```powershell
# Check if NVIDIA runtime is properly configured
docker info | Select-String nvidia

# Check NVIDIA driver status
nvidia-smi

# Restart NVIDIA Container Runtime (if available)
# This may require administrator privileges
```

### Solution 5: Alternative GPU Configuration
If the above solutions don't work, consider:
1. Using WSL2 with Docker instead of Docker Desktop
2. Installing NVIDIA Container Toolkit manually
3. Using OpenCL version instead of CUDA (if available)

## Current Workaround

### Use CPU Version for Now
```powershell
# Start CPU container
docker-compose up -d katago-cpu

# Test functionality
python test_katago.py

# Or use the Windows test script
python python_examples/windows_test.py
```

### Performance Comparison
- **CPU Version**: ~50-100 visits per analysis (slower but functional)
- **GPU Version**: ~500+ visits per analysis (much faster when working)

## Testing Tools Available

1. **`test_katago.py`**: Basic functionality test
2. **`python_examples/windows_test.py`**: Comprehensive analysis test
3. **`python_examples/stepbystep.py`**: Full SGF analysis (when working)

## Next Steps

1. **Immediate**: Continue using CPU version for development/testing
2. **Short-term**: Try the solutions above to fix GPU runtime
3. **Long-term**: Consider alternative GPU setups if issues persist

## Additional Notes

- The model file `models/model.bin.gz` is correctly configured
- All analysis configurations are working with CPU version
- The issue is specifically with NVIDIA Docker runtime, not KataGo itself
- CPU version provides full functionality, just at reduced speed

---

**Last Updated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Status**: CPU working, GPU troubleshooting in progress