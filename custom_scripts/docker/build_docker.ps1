# KataGo Docker Build Script (PowerShell Version)
# Multi-platform support: Mac, Windows, Linux
# Multi-backend support: CPU(EIGEN), NVIDIA GPU(CUDA), OpenCL

param(
    [string]$Backend = "",
    [switch]$AutoDetect,
    [switch]$Help
)

if ($Help) {
    Write-Host "KataGo Docker Build Script" -ForegroundColor Blue
    Write-Host "Usage: .\build_docker.ps1 [-Backend <EIGEN|CUDA|OPENCL>] [-AutoDetect] [-Help]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Backend     Specify backend type (EIGEN, CUDA, OPENCL)"
    Write-Host "  -AutoDetect  Auto-detect best backend"
    Write-Host "  -Help        Show this help message"
    exit 0
}

Write-Host "=== KataGo Docker Multi-Platform Build Script (Windows) ===" -ForegroundColor Blue

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop for Windows:"
    Write-Host "  Download: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
}

# Check if docker-compose is installed
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: docker-compose is not installed" -ForegroundColor Red
    Write-Host "Docker Desktop usually includes docker-compose, please check installation"
    exit 1
}

Write-Host "Detected OS: Windows" -ForegroundColor Blue

# GPU detection function
function Test-NvidiaGPU {
    try {
        $nvidiaOutput = nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -eq 0 -and $nvidiaOutput) {
            Write-Host "NVIDIA GPU detected" -ForegroundColor Green
            Write-Host "GPU: $($nvidiaOutput.Split([Environment]::NewLine)[0])"
            return $true
        }
    }
    catch {
        # nvidia-smi does not exist or failed
    }
    return $false
}

# Backend selection logic
if ($AutoDetect) {
    Write-Host "Auto-detecting best backend..." -ForegroundColor Blue
    if (Test-NvidiaGPU) {
        $USE_BACKEND = "CUDA"
        Write-Host "Auto-selected: NVIDIA GPU (CUDA)" -ForegroundColor Green
    } else {
        $USE_BACKEND = "EIGEN"
        Write-Host "Auto-selected: CPU (EIGEN)" -ForegroundColor Green
    }
} elseif ($Backend) {
    $USE_BACKEND = $Backend.ToUpper()
    switch ($USE_BACKEND) {
        "EIGEN" {
            Write-Host "Selected CPU backend" -ForegroundColor Green
        }
        "CUDA" {
            Write-Host "Selected NVIDIA GPU backend" -ForegroundColor Green
            if (!(Test-NvidiaGPU)) {
                Write-Host "Warning: No available NVIDIA GPU detected" -ForegroundColor Yellow
            }
        }
        "OPENCL" {
            Write-Host "Selected OpenCL backend" -ForegroundColor Green
        }
        default {
            Write-Host "Invalid backend selection: $Backend" -ForegroundColor Red
            Write-Host "Supported backends: EIGEN, CUDA, OPENCL"
            exit 1
        }
    }
} else {
    Write-Host "Select compute backend:" -ForegroundColor Yellow
    Write-Host "1) CPU (EIGEN) - Compatible with all platforms"
    Write-Host "2) NVIDIA GPU (CUDA) - Requires NVIDIA GPU"
    Write-Host "3) OpenCL - Supports various GPUs"
    Write-Host "4) Auto-detect"
    
    do {
        $choice = Read-Host "Please select [1-4]"
    } while ($choice -notmatch '^[1-4]$')
    
    switch ($choice) {
        "1" {
            $USE_BACKEND = "EIGEN"
            Write-Host "Selected CPU backend" -ForegroundColor Green
        }
        "2" {
            $USE_BACKEND = "CUDA"
            Write-Host "Selected NVIDIA GPU backend" -ForegroundColor Green
            if (!(Test-NvidiaGPU)) {
                Write-Host "Warning: No available NVIDIA GPU detected" -ForegroundColor Yellow
            }
        }
        "3" {
            $USE_BACKEND = "OPENCL"
            Write-Host "Selected OpenCL backend" -ForegroundColor Green
        }
        "4" {
            Write-Host "Auto-detecting best backend..." -ForegroundColor Blue
            if (Test-NvidiaGPU) {
                $USE_BACKEND = "CUDA"
                Write-Host "Auto-selected: NVIDIA GPU (CUDA)" -ForegroundColor Green
            } else {
                $USE_BACKEND = "EIGEN"
                Write-Host "Auto-selected: CPU (EIGEN)" -ForegroundColor Green
            }
        }
    }
}

# Build parameters
$USE_TCMALLOC = 1
$USE_AVX2 = 1
$BUILD_DISTRIBUTED = 0

Write-Host "Build parameters:" -ForegroundColor Blue
Write-Host "  Platform: Windows"
Write-Host "  USE_BACKEND: $USE_BACKEND"
Write-Host "  USE_TCMALLOC: $USE_TCMALLOC"
Write-Host "  USE_AVX2: $USE_AVX2"
Write-Host "  BUILD_DISTRIBUTED: $BUILD_DISTRIBUTED"
Write-Host ""

# Create necessary directories
$directories = @("models", "logs", "analysis_logs", "configs", "python_examples")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Gray
    }
}

# Build Docker images
Write-Host "Starting Docker image build..." -ForegroundColor Blue

# Set environment variables
$env:USE_BACKEND = $USE_BACKEND
$env:USE_TCMALLOC = $USE_TCMALLOC
$env:USE_AVX2 = $USE_AVX2
$env:BUILD_DISTRIBUTED = $BUILD_DISTRIBUTED

# Build appropriate services based on backend selection
switch ($USE_BACKEND) {
    "EIGEN" {
        Write-Host "Building CPU version..." -ForegroundColor Blue
        docker-compose build katago-cpu katago-gtp-cpu
    }
    "CUDA" {
        Write-Host "Building GPU version..." -ForegroundColor Blue
        docker-compose build katago-gpu katago-gtp-gpu
    }
    "OPENCL" {
        Write-Host "Building OpenCL version..." -ForegroundColor Blue
        docker-compose build katago-opencl
    }
    default {
        Write-Host "Building all versions..." -ForegroundColor Blue
        docker-compose build
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker image build successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Docker image build failed!" -ForegroundColor Red
    exit 1
}

# Check model files
if (!(Test-Path "models\*.bin.gz")) {
    Write-Host "Warning: No model files found in models/ directory" -ForegroundColor Yellow
    Write-Host "Please download KataGo model files and place them in models/ directory"
    Write-Host "Download: https://github.com/lightvector/KataGo/releases"
    Write-Host ""
}

Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Blue
Write-Host ""

# Provide usage instructions based on built backend
switch ($USE_BACKEND) {
    "EIGEN" {
        Write-Host "CPU Version Usage:" -ForegroundColor Yellow
        Write-Host "   # Start analysis engine"
        Write-Host "   docker-compose up -d katago-cpu"
        Write-Host "   docker-compose logs -f katago-cpu"
        Write-Host ""
        Write-Host "   # Start GTP engine"
        Write-Host "   docker-compose up -d katago-gtp-cpu"
        Write-Host "   docker-compose logs -f katago-gtp-cpu"
    }
    "CUDA" {
        Write-Host "GPU Version Usage:" -ForegroundColor Yellow
        Write-Host "   # Start analysis engine"
        Write-Host "   docker-compose up -d katago-gpu"
        Write-Host "   docker-compose logs -f katago-gpu"
        Write-Host ""
        Write-Host "   # Start GTP engine"
        Write-Host "   docker-compose up -d katago-gtp-gpu"
        Write-Host "   docker-compose logs -f katago-gtp-gpu"
        Write-Host ""
        Write-Host "Windows GPU Notes:" -ForegroundColor Blue
        Write-Host "- Ensure NVIDIA Container Toolkit is installed"
        Write-Host "- Ensure Docker Desktop uses WSL2 backend"
        Write-Host "- Test GPU access: docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi"
        Write-Host ""
    }
    "OPENCL" {
        Write-Host "OpenCL Version Usage:" -ForegroundColor Yellow
        Write-Host "   # Start analysis engine"
        Write-Host "   docker-compose up -d katago-opencl"
        Write-Host "   docker-compose logs -f katago-opencl"
    }
}

Write-Host "Development Environment:" -ForegroundColor Yellow
Write-Host "   # Start development environment"
Write-Host "   `$env:KATAGO_BACKEND='$USE_BACKEND'; docker-compose up -d katago-dev"
Write-Host "   docker-compose exec katago-dev /bin/bash"
Write-Host ""
Write-Host "Python Examples:" -ForegroundColor Yellow
Write-Host "   docker-compose exec katago-dev python3 /app/python_examples/example.py"
Write-Host ""
Write-Host "Important Notes:" -ForegroundColor Blue
Write-Host "- Ensure models/ directory contains valid model files"
Write-Host "- Log files will be saved in logs/ and analysis_logs/ directories"
Write-Host "- Customize settings by modifying config files in configs/ directory"
Write-Host "- See DOCKER_USAGE.md for detailed usage instructions"
Write-Host ""
Write-Host "Platform Compatibility:" -ForegroundColor Green
Write-Host "- CPU version: Compatible with Mac, Windows, Linux"
Write-Host "- GPU version: Compatible with Windows + NVIDIA GPU, Linux + NVIDIA GPU"
Write-Host "- OpenCL version: Compatible with OpenCL-supported systems"