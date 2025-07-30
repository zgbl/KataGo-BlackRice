# 多阶段构建 - 构建阶段
# 支持多平台：使用条件基础镜像
ARG USE_BACKEND=EIGEN
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE} AS builder

# 设置环境变量避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 构建参数
ARG USE_BACKEND=EIGEN
ARG USE_TCMALLOC=1
ARG USE_AVX2=0
ARG BUILD_DISTRIBUTED=0
ARG TARGETPLATFORM

# 安装基础构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ninja-build \
    pkg-config \
    libzip-dev \
    zlib1g-dev \
    libeigen3-dev \
    libssl-dev \
    libgoogle-perftools-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 条件安装CUDA支持（仅在需要时）
RUN if [ "$USE_BACKEND" = "CUDA" ] || [ "$USE_BACKEND" = "TENSORRT" ]; then \
        apt-get update && apt-get install -y \
        software-properties-common \
        && wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb \
        && dpkg -i cuda-keyring_1.1-1_all.deb \
        && apt-get update \
        && apt-get install -y \
        cuda-toolkit-12-9 \
        && rm -rf /var/lib/apt/lists/* \
        && rm cuda-keyring_1.1-1_all.deb; \
    fi

# 条件安装cuDNN（仅在CUDA后端时）
RUN if [ "$USE_BACKEND" = "CUDA" ] || [ "$USE_BACKEND" = "TENSORRT" ]; then \
        wget https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/linux-x86_64/cudnn-linux-x86_64-9.6.0.74_cuda12-archive.tar.xz \
        && tar -xf cudnn-linux-x86_64-9.6.0.74_cuda12-archive.tar.xz \
        && cp cudnn-linux-x86_64-9.6.0.74_cuda12-archive/include/cudnn*.h /usr/local/cuda/include/ \
        && cp cudnn-linux-x86_64-9.6.0.74_cuda12-archive/lib/libcudnn* /usr/local/cuda/lib64/ \
        && chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn* \
        && rm -rf cudnn-linux-x86_64-9.6.0.74_cuda12-archive* \
        && echo '/usr/local/cuda/lib64' >> /etc/ld.so.conf.d/cuda.conf \
        && ldconfig; \
    fi

# 条件安装OpenCL支持（仅在需要时）
RUN if [ "$USE_BACKEND" = "OPENCL" ]; then \
        apt-get update && apt-get install -y \
        ocl-icd-opencl-dev \
        opencl-headers \
        clinfo \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# 设置工作目录
WORKDIR /app

# 复制源代码
COPY . .

# 编译KataGo
WORKDIR /app/cpp

# 设置CUDA环境变量（如果使用CUDA）
RUN if [ "$USE_BACKEND" = "CUDA" ] || [ "$USE_BACKEND" = "TENSORRT" ]; then \
        export PATH=/usr/local/cuda/bin:$PATH \
        && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH; \
    fi

# 条件编译：根据后端类型进行编译
RUN if [ "$USE_BACKEND" = "CUDA" ] || [ "$USE_BACKEND" = "TENSORRT" ]; then \
        export PATH=/usr/local/cuda/bin:$PATH \
        && export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH \
        && cmake . \
            -G Ninja \
            -DUSE_BACKEND=${USE_BACKEND} \
            -DUSE_TCMALLOC=${USE_TCMALLOC} \
            -DUSE_AVX2=${USE_AVX2} \
            -DBUILD_DISTRIBUTED=${BUILD_DISTRIBUTED} \
            -DCMAKE_BUILD_TYPE=Release \
            -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
            -DCUDNN_INCLUDE_DIR=/usr/local/cuda/include \
            -DCUDNN_LIBRARY=/usr/local/cuda/lib64/libcudnn.so \
        && ninja; \
    else \
        cmake . \
            -G Ninja \
            -DUSE_BACKEND=${USE_BACKEND} \
            -DUSE_TCMALLOC=${USE_TCMALLOC} \
            -DUSE_AVX2=${USE_AVX2} \
            -DBUILD_DISTRIBUTED=${BUILD_DISTRIBUTED} \
            -DCMAKE_BUILD_TYPE=Release \
        && ninja; \
    fi

# 运行阶段
ARG USE_BACKEND=EIGEN
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE} AS runtime

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 传递构建参数到运行时
ARG USE_BACKEND=EIGEN

# 安装基础运行时依赖
RUN apt-get update && apt-get install -y \
    libzip4 \
    zlib1g \
    libssl3 \
    libgoogle-perftools4 \
    curl \
    wget \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# CUDA运行时已包含在基础镜像中（当USE_BACKEND=CUDA时）
# 确保CUDA库路径正确配置
RUN if [ "$USE_BACKEND" = "CUDA" ] || [ "$USE_BACKEND" = "TENSORRT" ]; then \
        echo '/usr/local/cuda/lib64' >> /etc/ld.so.conf.d/cuda.conf \
        && ldconfig; \
    fi

# 条件安装OpenCL运行时（仅在OpenCL后端时）
RUN if [ "$USE_BACKEND" = "OPENCL" ]; then \
        apt-get update && apt-get install -y \
        ocl-icd-libopencl1 \
        clinfo \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# 安装Python依赖（用于分析引擎示例）
RUN pip3 install --no-cache-dir \
    numpy \
    sgfmill

# 创建应用目录
WORKDIR /app

# 从构建阶段复制可执行文件
COPY --from=builder /app/cpp/katago /usr/local/bin/katago

# 复制配置文件和示例
COPY --from=builder /app/cpp/tests/data/configs/analysis_example.cfg /app/configs/
COPY --from=builder /app/python/query_analysis_engine_example.py /app/
COPY --from=builder /app/docs/Analysis_Engine.md /app/docs/

# 创建必要的目录
RUN mkdir -p /app/models /app/logs /app/analysis_logs

# 复制启动脚本
COPY http_server/scripts/start_http_server.sh /app/start_analysis.sh
RUN chmod +x /app/start_analysis.sh

# 创建GTP模式启动脚本
RUN echo '#!/bin/bash' > /app/start_gtp.sh && \
    echo '' >> /app/start_gtp.sh && \
    echo '# 检查模型文件' >> /app/start_gtp.sh && \
    echo 'if [ ! -f "/app/models/model.bin.gz" ]; then' >> /app/start_gtp.sh && \
    echo '    echo "错误: 未找到模型文件 /app/models/model.bin.gz"' >> /app/start_gtp.sh && \
    echo '    echo "请将模型文件挂载到容器的 /app/models/ 目录"' >> /app/start_gtp.sh && \
    echo '    exit 1' >> /app/start_gtp.sh && \
    echo 'fi' >> /app/start_gtp.sh && \
    echo '' >> /app/start_gtp.sh && \
    echo '# 生成GTP配置' >> /app/start_gtp.sh && \
    echo 'katago genconfig \' >> /app/start_gtp.sh && \
    echo '    -model /app/models/model.bin.gz \' >> /app/start_gtp.sh && \
    echo '    -output /app/configs/gtp_generated.cfg' >> /app/start_gtp.sh && \
    echo '' >> /app/start_gtp.sh && \
    echo '# 启动GTP引擎' >> /app/start_gtp.sh && \
    echo 'echo "启动KataGo GTP引擎..."' >> /app/start_gtp.sh && \
    echo 'exec katago gtp \' >> /app/start_gtp.sh && \
    echo '    -config /app/configs/gtp_generated.cfg \' >> /app/start_gtp.sh && \
    echo '    -model /app/models/model.bin.gz \' >> /app/start_gtp.sh && \
    echo '    "$@"' >> /app/start_gtp.sh && \
    chmod +x /app/start_gtp.sh

# 创建Python示例启动脚本
RUN echo '#!/bin/bash' > /app/run_example.sh && \
    echo '' >> /app/run_example.sh && \
    echo '# 检查模型文件' >> /app/run_example.sh && \
    echo 'if [ ! -f "/app/models/model.bin.gz" ]; then' >> /app/run_example.sh && \
    echo '    echo "错误: 未找到模型文件 /app/models/model.bin.gz"' >> /app/run_example.sh && \
    echo '    echo "请将模型文件挂载到容器的 /app/models/ 目录"' >> /app/run_example.sh && \
    echo '    exit 1' >> /app/run_example.sh && \
    echo 'fi' >> /app/run_example.sh && \
    echo '' >> /app/run_example.sh && \
    echo '# 运行Python示例' >> /app/run_example.sh && \
    echo 'echo "运行KataGo分析引擎Python示例..."' >> /app/run_example.sh && \
    echo 'python3 /app/query_analysis_engine_example.py \' >> /app/run_example.sh && \
    echo '    --katago-path /usr/local/bin/katago \' >> /app/run_example.sh && \
    echo '    --config-path /app/configs/analysis_example.cfg \' >> /app/run_example.sh && \
    echo '    --model-path /app/models/model.bin.gz \' >> /app/run_example.sh && \
    echo '    "$@"' >> /app/run_example.sh && \
    chmod +x /app/run_example.sh

# 暴露端口（如果需要HTTP服务）
EXPOSE 8080

# 设置默认命令
CMD ["/app/start_analysis.sh"]