# KataGo - BlackRice Tech Edition

> **🏢 BlackRice Tech 定制版本**  
> 这是由 BlackRice Tech 公司基于开源 KataGo 项目开发的定制版本，专为企业级围棋AI应用和分析引擎开发而优化。

---

## 🚀 BlackRice Tech 版本特性

- **🐳 Docker 化部署**: 完整的容器化解决方案，支持快速部署和扩展
- **⚡ 企业级优化**: 针对高并发分析场景的性能优化
- **🔧 开发者友好**: 增强的API接口和开发工具
- **📊 分析引擎增强**: 优化的JSON分析引擎，支持批量处理
- **🛠️ 定制化配置**: 企业级配置管理和监控

## 📋 目录

* [BlackRice Tech 版本特性](#blackrice-tech-版本特性)
* [概述](#概述)
* [训练历史和研究](#训练历史和研究)
* [下载资源](#下载资源)
* [安装和运行 KataGo](#安装和运行-katago)
  * [图形界面](#图形界面)
  * [Windows 和 Linux](#windows-和-linux)
  * [MacOS](#macos)
  * [OpenCL vs CUDA vs TensorRT vs Eigen](#opencl-vs-cuda-vs-tensorrt-vs-eigen)
  * [使用方法](#使用方法)
  * [性能调优](#性能调优)
  * [常见问题](#常见问题)
    * [特定GPU或驱动问题](#特定gpu或驱动问题)
    * [常见问题](#常见问题-1)
    * [其他问题](#其他问题)
* [开发者功能](#开发者功能)
  * [GTP 扩展](#gtp-扩展)
  * [分析引擎](#分析引擎)
* [编译 KataGo](#编译-katago)
* [源码概览](#源码概览)
* [自对弈训练](#自对弈训练)
* [贡献者](#贡献者)
* [许可证](#许可证)

## 概述

**BlackRice Tech 版本说明**: 本版本基于 KataGo 开源项目进行定制开发，专注于企业级应用场景。我们保持与上游项目的兼容性，同时添加了企业级功能和优化。

KataGo 是目前最强的开源围棋AI引擎之一。KataGo 使用类似 AlphaZero 的训练过程，并包含许多增强和改进，能够快速达到顶级水平，完全从零开始，无需外部数据，仅通过自对弈改进。这些改进中的一些利用了游戏特定的特征和训练目标，但许多技术是通用的，可以应用于其他游戏。因此，早期训练比其他自对弈训练的机器人快得多 - 只需几个强大的GPU几天时间，任何研究人员/爱好者都应该能够从零开始训练神经网络到高业余段位水平。如果调优得当，仅使用*单个*顶级消费级GPU的训练运行可能在几个月内将机器人从零训练到超人类强度。

KataGo 的引擎旨在成为围棋玩家和开发者的有用工具，支持以下功能：
* 估算领地和得分，而不仅仅是"胜率"，帮助分析业余段位游戏，而不仅仅是在职业/超人类水平上实际影响游戏结果的着法。
* 关心最大化得分，在让子棋中落后时能够强力对战，在终局获胜时减少松懈着法。
* 支持不同的贴目值（包括整数值）和良好的高让子游戏对弈。
* 支持从7x7到19x19的棋盘大小，截至2020年5月，可能是9x9和13x13上最强的开源机器人。
* 支持各种[规则](https://lightvector.github.io/KataGo/rules.html)，包括在几乎所有常见情况下匹配日本规则的规则，以及古代数子规则。
* 对于工具/后端开发者 - 支持基于JSON的分析引擎，可以高效批处理多游戏评估，比GTP更易于使用。

## 训练历史和研究

以下是一些关于 KataGo 研究和训练的文档/论文/帖子链接！

* 关于 KataGo 中使用的主要新思想和技术的论文：[Accelerating Self-Play Learning in Go (arXiv)](https://arxiv.org/abs/1902.10565)。许多具体参数已过时，但一般方法继续使用。

* 自那时以来发现了许多重大改进，这些改进已纳入 KataGo 最近的运行中，并在此处记录：[KataGoMethods.md](docs/KataGoMethods.md)。

* KataGo 有一个完全工作的蒙特卡洛图搜索实现，将MCTS扩展到在图上而不仅仅是树上操作！解释可以在这里找到 [Monte-Carlo Graph Search from First Principles](docs/GraphSearch.md)。这个解释是通用的（不特定于KataGo），旨在填补学术文献中解释材料的巨大空白，希望对其他人有用！

* 非常感谢 [Jane Street](https://www.janestreet.com/) 支持 KataGo 主要早期发布运行的训练，以及众多较小的测试运行和实验。关于初始发布和一些有趣后续实验的博客文章：
    * [Accelerating Self-Play Learning in Go](https://blog.janestreet.com/accelerating-self-play-learning-in-go/)
    * [Deep-Learning the Hardest Go Problem in the World](https://blog.janestreet.com/deep-learning-the-hardest-go-problem-in-the-world/)。

有关 KataGo 较旧训练运行的更多详细信息，包括与其他机器人的比较，请参阅 [Older Training History and Research](TrainingHistory.md)！

如果您想询问关于 KataGo 或其工作原理的一般信息，或关于除 KataGo 之外的一些过去的围棋机器人，请考虑计算机围棋 [discord频道](https://discord.gg/bqkZAz3)。

## 下载资源

**BlackRice Tech 版本**: 请从我们的企业仓库获取最新的预编译可执行文件和模型。

原版 KataGo 的预编译可执行文件可以在 [releases page](https://github.com/lightvector/KataGo/releases) 找到，支持 Windows 和 Linux。

最新的神经网络可在 [https://katagotraining.org/](https://katagotraining.org/) 获得。

## 安装和运行 KataGo

**BlackRice Tech Docker 部署**: 我们推荐使用提供的 Docker 解决方案进行快速部署：

```bash
# 构建 Docker 镜像
./build_docker.sh

# 运行分析引擎
docker-compose run --rm katago-analysis

# 运行 GTP 引擎
docker-compose run --rm katago-gtp

# 开发环境
docker-compose run --rm katago-dev
```

KataGo 实现的是 GTP 引擎，这是围棋软件使用的简单文本协议。它本身没有图形界面。因此，通常您需要将 KataGo 与 GUI 或分析程序一起使用。其中一些在下载中捆绑了 KataGo，这样您就可以从一个地方获得所有内容，而不是分别下载和管理文件路径和命令。

### 图形界面
这绝不是一个完整的列表 - 有很多东西。但是，截至2020年，一些更容易和/或流行的可能是：

* [KaTrain](https://github.com/sanderland/katrain) - KaTrain 对于非技术用户来说可能是最容易设置的，提供一体化包（无需单独下载 KataGo！），为较弱玩家提供修改强度的机器人，以及良好的分析功能。
* [Lizzie](https://github.com/featurecat/lizzie) - Lizzie 在运行长时间交互式分析和实时可视化方面非常受欢迎。Lizzie 也提供一体化包。但是请记住，KataGo 的 OpenCL 版本在第一次启动时可能需要相当长的时间来调优和加载，如[这里](#opencl-vs-cuda)所述，Lizzie 在显示这个进度时做得很差。在实际错误或失败的情况下，Lizzie 的界面不是最好的解释这些错误，会看起来永远挂起。与 Lizzie 打包的 KataGo 版本相当强，但可能不总是最新或最强的，所以一旦您让它工作，您可能想要从 [releases page](https://github.com/lightvector/KataGo/releases) 下载 KataGo 和更新的网络，并用它们替换 Lizzie 的版本。
* [Ogatak](https://github.com/rooklift/ogatak) 是一个 KataGo 特定的 GUI，强调以快速、响应的方式显示基础知识。它不包含 KataGo。
* [q5Go](https://github.com/bernds/q5Go) 和 [Sabaki](https://sabaki.yichuanshen.de/) 是支持 KataGo 的通用 SGF 编辑器和 GUI，包括 KataGo 的得分估算和许多高质量功能。

通常，对于不提供一体化包的 GUI，您需要下载 KataGo（或您选择的任何其他围棋引擎！）并告诉 GUI 运行引擎的正确命令行，包含正确的文件路径。有关 KataGo 命令行界面的详细信息，请参阅下面的[使用方法](#使用方法)。

### Windows 和 Linux

KataGo 目前正式支持 Windows 和 Linux，[每个版本都提供预编译可执行文件](https://github.com/lightvector/KataGo/releases)。在 Windows 上，可执行文件通常应该开箱即用，在 Linux 上，如果您遇到系统库版本问题，作为替代方案，[从源码构建](Compiling.md) 通常很简单。并非所有不同的操作系统版本和编译器都经过测试，所以如果您遇到问题，请随时开启一个 issue。KataGo 当然也可以在 Windows 上通过 MSVC 或在 Linux 上通过 g++ 等常用编译器从源码编译，进一步记录如下。

### MacOS
社区还为 MacOS 上的 [Homebrew](https://brew.sh) 提供 KataGo 包 - 那里的发布可能会稍微滞后于官方发布。

使用 `brew install katago`。最新的配置文件和网络安装在 KataGo 的 `share` 目录中。通过 `brew list --verbose katago` 找到它们。运行 katago 的基本方法是 `katago gtp -config $(brew list --verbose katago | grep 'gtp.*\.cfg') -model $(brew list --verbose katago | grep .gz | head -1)`。您应该根据这里的发布说明选择网络，并像安装 KataGo 的其他方式一样自定义提供的示例配置。

### OpenCL vs CUDA vs TensorRT vs Eigen
KataGo 有四个后端：OpenCL（GPU）、CUDA（GPU）、TensorRT（GPU）和 Eigen（CPU）。

快速总结是：
  * **要轻松获得工作的东西，如果您有任何好的或不错的GPU，请尝试 OpenCL。**
  * **对于 NVIDIA GPU 通常更好的性能，请尝试 TensorRT**，但您可能需要从 Nvidia 安装 TensorRT。
  * 如果您没有 GPU 或您的 GPU 太旧/太弱无法与 OpenCL 一起工作，并且您只想要一个纯 CPU KataGo，请使用带 AVX2 的 Eigen。
  * 如果您的 CPU 很旧或在不支持 AVX2 的低端设备上，请使用不带 AVX2 的 Eigen。
  * CUDA 后端可以与安装了 CUDA+CUDNN 的 NVIDIA GPU 一起工作，但可能比 TensorRT 差。

更详细地：
  * OpenCL 是一个通用 GPU 后端，应该能够与任何支持 [OpenCL](https://en.wikipedia.org/wiki/OpenCL) 的 GPU 或加速器一起运行，包括 NVIDIA GPU、AMD GPU，以及基于 CPU 的 OpenCL 实现或 Intel 集成显卡等。这是 KataGo 最通用的 GPU 版本，不需要像 CUDA 那样复杂的安装，所以只要您有相当现代的 GPU，最有可能开箱即用。**但是，它也需要在第一次运行时花一些时间来调优自己。** 对于许多系统，这将需要5-30秒，但在一些较旧/较慢的系统上，可能需要许多分钟或更长时间。此外，OpenCL 实现的质量有时不一致，特别是对于 Intel 集成显卡和几年前的 AMD GPU，所以它可能不适用于非常旧的机器，以及特定有问题的较新 AMD GPU，另请参阅[特定GPU或驱动问题](#特定gpu或驱动问题)。
  * CUDA 是特定于 NVIDIA GPU 的 GPU 后端（它不适用于 AMD 或 Intel 或任何其他 GPU），需要安装 [CUDA](https://developer.nvidia.com/cuda-zone) 和 [CUDNN](https://developer.nvidia.com/cudnn) 以及现代 NVIDIA GPU。在大多数 GPU 上，OpenCL 实现实际上会在性能上击败 NVIDIA 自己的 CUDA/CUDNN。例外是支持 FP16 和张量核心的顶级 NVIDIA GPU，在这种情况下，有时一个更好，有时另一个更好。
  * TensorRT 类似于 CUDA，但仅使用 NVIDIA 的 TensorRT 框架来运行具有更优化内核的神经网络。对于现代 NVIDIA GPU，它应该在 CUDA 工作的任何地方工作，并且通常比 CUDA 或任何其他后端更快。
  * Eigen 是一个 *CPU* 后端，应该广泛工作 *无需* GPU 或花哨的驱动程序。如果您没有好的 GPU 或根本没有 GPU，请使用此选项。它会比 OpenCL 或 CUDA 慢得多，但在好的 CPU 上，如果使用较小的（15或20）块神经网络，仍然经常可以获得每秒10到20次推演。Eigen 也可以用 AVX2 和 FMA 支持编译，这可以为过去几年的 Intel 和 AMD CPU 提供很大的性能提升。但是，它根本不会在不支持这些花哨向量指令的较旧 CPU（甚至可能一些最近但低功耗的现代 CPU）上运行。

对于**任何**实现，如果您关心最佳性能，建议您也调优使用的线程数，因为它可以在速度上产生2-3倍的差异。请参阅下面的"性能调优"。但是，如果您主要只是想让它工作，那么默认的未调优设置也应该仍然合理。

### 使用方法
KataGo 只是一个引擎，没有自己的图形界面。因此，通常您需要将 KataGo 与 [GUI 或分析程序](#图形界面) 一起使用。
如果您在设置过程中遇到任何问题，请查看[常见问题](#常见问题)。

**首先**：运行这样的命令来确保 KataGo 正在工作，使用您[下载](https://github.com/lightvector/KataGo/releases/tag/v1.4.5)的神经网络文件。在 OpenCL 上，它也会为您的 GPU 调优。
```
./katago.exe benchmark                                                   # if you have default_gtp.cfg and default_model.bin.gz
./katago.exe benchmark -model <NEURALNET>.bin.gz                         # if you have default_gtp.cfg
./katago.exe benchmark -model <NEURALNET>.bin.gz -config gtp_custom.cfg  # use this .bin.gz neural net and this .cfg file
```
It will tell you a good number of threads. Edit your .cfg file and set "numSearchThreads" to that many to get best performance.

**Or**: Run this command to have KataGo generate a custom gtp config for you based on answering some questions:
```
./katago.exe genconfig -model <NEURALNET>.bin.gz -output gtp_custom.cfg
```

**Next**: A command like this will run KataGo's engine. This is the command to give to your [GUI or analysis program](#guis) so that it can run KataGo.
```
./katago.exe gtp                                                   # if you have default_gtp.cfg and default_model.bin.gz
./katago.exe gtp -model <NEURALNET>.bin.gz                         # if you have default_gtp.cfg
./katago.exe gtp -model <NEURALNET>.bin.gz -config gtp_custom.cfg  # use this .bin.gz neural net and this .cfg file
```

You may need to specify different paths when entering KataGo's command for a GUI program, e.g.:
```
path/to/katago.exe gtp -model path/to/<NEURALNET>.bin.gz
path/to/katago.exe gtp -model path/to/<NEURALNET>.bin.gz -config path/to/gtp_custom.cfg
```

#### Human-style Play and Analysis

You can also have KataGo imitate human play if you download the human SL model b18c384nbt-humanv0.bin.gz from https://github.com/lightvector/KataGo/releases/tag/v1.15.0, and run a command like the following, providing both the normal model and the human SL model:
```
./katago.exe gtp -model <NEURALNET>.bin.gz -human-model b18c384nbt-humanv0.bin.gz -config gtp_human5k_example.cfg
```

The [gtp_human5k_example.cfg](cpp/configs/gtp_human5k_example.cfg) configures KataGo to imitate 5-kyu-level players. You can change it to imitate other ranks too, as well as to do many more things, including making KataGo play in a human style but still at a strong level or analyze in interesting ways. Read the config file itself for documentation on some of these possibilities!

And see also [this guide](https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md#human-sl-analysis-guide) to using the human SL model, which is written from the perspective of the JSON-based analysis engine mentioned below, but is also applicable to gtp as well.

#### Other Commands:

Run a JSON-based [analysis engine](docs/Analysis_Engine.md) that can do efficient batched evaluations for a backend Go service:

   * `./katago analysis -model <NEURALNET>.gz -config <ANALYSIS_CONFIG>.cfg`

Run a high-performance match engine that will play a pool of bots against each other sharing the same GPU batches and CPUs with each other:

   * `./katago match -config <MATCH_CONFIG>.cfg -log-file match.log -sgf-output-dir <DIR TO WRITE THE SGFS>`

Force OpenCL tuner to re-tune:

   * `./katago tuner -config <GTP_CONFIG>.cfg`

Print version:

   * `./katago version`


### Tuning for Performance

The most important parameter to optimize for KataGo's performance is the number of threads to use - this can easily make a factor of 2 or 3 difference.

Secondarily, you can also read over the parameters in your GTP config (`default_gtp.cfg` or `gtp_example.cfg` or `configs/gtp_example.cfg`, etc). A lot of other settings are described in there that you can set to adjust KataGo's resource usage, or choose which GPUs to use. You can also adjust things like KataGo's resign threshold, pondering behavior or utility function. Most parameters are documented directly inline in the [example config file](cpp/configs/gtp_example.cfg). Many can also be interactively set when generating a config via the `genconfig` command described above.


### Common Questions and Issues
This section summarizes a number of common questions and issues when running KataGo.

#### Issues with specific GPUs or GPU drivers
If you are observing any crashes in KataGo while attempting to run the benchmark or the program itself, and you have one of the below GPUs, then this is likely the reason.

* **AMD Radeon RX 5700** - AMD's drivers for OpenCL for this GPU have been buggy ever since this GPU was released, and as of May 2020 AMD has still never released a fix. If you are using this GPU, you will just not be able to run KataGo (Leela Zero and other Go engines will probably fail too) and will probably also obtain incorrect calculations or crash if doing anything else scientific or mathematical that uses OpenCL. See for example these reddit threads: [[1]](https://www.reddit.com/r/Amd/comments/ebso1x/its_not_just_setihome_any_mathematic_or/) or [[2]](https://www.reddit.com/r/BOINC/comments/ebiz18/psa_please_remove_your_amd_rx5700xt_from_setihome/) or this [L19 thread](https://lifein19x19.com/viewtopic.php?f=18&t=17093).
* **OpenCL Mesa** - These drivers for OpenCL are buggy. Particularly if on startup before crashing you see KataGo printing something like
`Found OpenCL Platform 0: ... (Mesa) (OpenCL 1.1 Mesa ...) ...`
then you are using the Mesa drivers. You will need to change your drivers, see for example this [KataGo issue](https://github.com/lightvector/KataGo/issues/182#issuecomment-607943405) which links to [this thread](https://bbs.archlinux.org/viewtopic.php?pid=1895516#p1895516).
* **Intel Integrated Graphics** - For weaker/older machines or laptops or devices that don't have a dedicated GPU, KataGo might end up using the weak "Intel Integrated Graphics" that is built in with the CPU. Often this will work fine (although KataGo will be slow and only get a tiny number of playouts compared to using a real GPU), but various versions of Intel Integrated Graphics can also be buggy and not work at all. If a driver update doesn't work for you, then the only solution is to upgrade to a better GPU. See for example this [issue](https://github.com/lightvector/KataGo/issues/54) or this [issue](https://github.com/lightvector/KataGo/issues/78), or this [other Github's issue](https://github.com/CNugteren/CLBlast/issues/280).

#### Common Problems
* **KataGo seems to hang or is "loading" forever on startup in Lizzie/Sabaki/q5go/GoReviewPartner/etc.**
   * Likely either you have some misconfiguration, have specified file paths incorrectly, a bad GPU, etc. Many of these GUIs do a poor job of reporting errors and may completely swallow the error message from KataGo that would have told you what was wrong. Try running KataGo's `benchmark` or `gtp` directly on the command line, as described [above](#how-to-use).
   * Sometimes there is no error at all, it is merely that the *first* time KataGo runs on a given network size, it needs to do some expensive tuning, which may take a few minutes. Again this is clearer if you run the `benchmark` command directly in the command line. After tuning, then subsequent runs will be faster.

* **KataGo works on the command line but having trouble specifying the right file paths for the GUI.**
   * As described [above](#how-to-use), you can name your config `default_gtp.cfg` and name whichever network file you've downloaded to `default_model.bin.gz` (for newer `.bin.gz` models) or `default_model.txt.gz` (for older `.txt.gz` models). Stick those into the same directory as KataGo's executable, and then you don't need to specify `-config` or `-model` paths at all.

* **KataGo gives an error like `Could not create file` when trying to run the initial tuning.**
   * KataGo probably does not have access permissions to write files in the directory where you placed it.
   * On Windows for example, the `Program Files` directory and its subdirectories are often restricted to only allow writes with admin-level permissions. Try placing KataGo somewhere else.

* **I'm new to the command line and still having trouble knowing what to tell Lizzie/q5go/Sabaki/whatever to make it run KataGo**.
   * Again, make sure you have your directory paths right.
   * A common issue: AVOID having any spaces in any file or directory names anywhere, since depending on the GUI, this may require you to have to quote or character-escape the paths or arguments in various ways.
   * If you don't understand command line arguments and flags, relative vs absolute file paths, etc, search online. Try pages like https://superuser.com/questions/1270591/how-to-use-relative-paths-on-windows-cmd or https://www.bleepingcomputer.com/tutorials/understanding-command-line-arguments-and-how-to-use-them/ or other pages you find, or get someone tech-savvy to help you in a chat or even in-person if you can.
   * Consider using https://github.com/sanderland/katrain instead - this is an excellent GUI written by someone else for KataGo that usually automates all of the technical setup for you.

* **I'm getting a different error or still want further help.**
   * Check out [the discord chat where Leela Zero, KataGo, and other bots hang out](https://discord.gg/bqkZAz3) and ask in the "#help" channel.
   * If you think you've found a bug in KataGo itself, feel free also to [open an issue](https://github.com/lightvector/KataGo/issues). Please provide as much detail as possible about the exact commands you ran, the full error message and output (if you're in a GUI, please make sure to check that GUI's raw GTP console or log), the things you've tried, your config file and network, your GPU and operating system, etc.

#### Other Questions
* **How do I make KataGo use Japanese rules or other rules?**
   * KataGo supports some [GTP extensions](docs/GTP_Extensions.md) for developers of GUIs to set the rules, but unfortunately as of June 2020, only a few of them make use of this. So as a workaround, there are a few ways:
     * Edit KataGo's config (`default_gtp.cfg` or `gtp_example.cfg` or `gtp.cfg`, or whatever you've named it) to use `rules=japanese` or `rules=chinese` or whatever you need, or set the individual rules `koRule`,`scoringRule`,`taxRule`, etc. to what they should be. See [here](https://github.com/lightvector/KataGo/blob/master/cpp/configs/gtp_example.cfg#L91) for where this is in the config, or and see [this webpage](https://lightvector.github.io/KataGo/rules.html) for the full description of KataGo's ruleset.
     * Use the `genconfig` command (`./katago genconfig -model <NEURALNET>.gz -output <PATH_TO_SAVE_GTP_CONFIG>.cfg`) to generate a config, and it will interactively help you, including asking you for what default rules you want.
     * If your GUI allows access directly to the GTP console (for example, press `E` in Lizzie), then you can run `kata-set-rules japanese` or similar for other rules directly in the GTP console, to change the rules dynamically in the middle of a game or an analysis session.

* **Which model/network should I use?**
   * Generally, use the strongest or most recent b18-sized net (b18c384nbt) from [the main training site](https://katagotraining.org/). This will be the best neural net even for weaker machines, since despite being a bit slower than old smaller nets, it is much stronger and more accurate per evaluation.
   * If you care a lot about theoretical purity - no outside data, bot learns strictly on its own - use the 20 or 40 block nets from [this release](https://github.com/lightvector/KataGo/releases/tag/v1.4.0), which are pure in this way and still much stronger than Leela Zero, but also much weaker than more recent nets.
   * If you want some nets that are much faster to run, and each with their own interesting style of play due to their unique stages of learning, try any of the "b10c128" or "b15c192" Extended Training Nets [here](https://katagoarchive.org/g170/neuralnets/index.html) which are 10 block and 15 block networks from earlier in the run that are much weaker but still pro-level-and-beyond.


## Features for Developers

#### GTP Extensions:
In addition to a basic set of [GTP commands](https://www.lysator.liu.se/~gunnar/gtp/), KataGo supports a few additional commands, for use with analysis tools and other programs.

KataGo's GTP extensions are documented **[here](docs/GTP_Extensions.md)**.

   * Notably: KataGo exposes a GTP command `kata-analyze` that in addition to policy and winrate, also reports an estimate of the *expected score* and a heatmap of the predicted territory ownership of every location of the board. Expected score should be particularly useful for reviewing handicap games or games of weaker players. Whereas the winrate for black will often remain pinned at nearly 100% in a handicap game even as black makes major mistakes (until finally the game becomes very close), expected score should make it more clear which earlier moves are losing points that allow white to catch up, and exactly how much or little those mistakes lose. If you're interested in adding support for this to any analysis tool, feel free to reach out, I'd be happy to answer questions and help.

   * KataGo also exposes a few GTP extensions that allow setting what rules are in effect (Chinese, AGA, Japanese, etc). See again [here](docs/GTP_Extensions.md) for details.

#### Analysis Engine:
KataGo also implements a separate engine that can evaluate much faster due to batching if you want to analyze whole games at once and might be much less of a hassle than GTP if you are working in an environment where JSON parsing is easy. See [here](docs/Analysis_Engine.md) for details.

KataGo also includes example code demonstrating how you can invoke the analysis engine from Python, see [here](python/query_analysis_engine_example.py)!

## Compiling KataGo
KataGo is written in C++. It should compile on Linux or OSX via g++ that supports at least C++14, or on Windows via MSVC 15 (2017) and later. Instructions may be found at [Compiling KataGo](Compiling.md).

## Source Code Overview:
See the [cpp readme](cpp/README.md) or the [python readme](python/README.md) for some high-level overviews of the source code in this repo, if you want to get a sense of what is where and how it fits together.

## Selfplay Training:
If you'd also like to run the full self-play loop and train your own neural nets using the code here, see [Selfplay Training](SelfplayTraining.md).

## Contributors

Many thanks to the various people who have contributed to this project! See [CONTRIBUTORS](CONTRIBUTORS) for a list of contributors.

## License

Except for several external libraries that have been included together in this repo under `cpp/external/` as well as the single file `cpp/core/sha2.cpp`, which all have their own individual licenses, all code and other content in this repo is released for free use or modification under the license in the following file: [LICENSE](LICENSE).

License aside, if you end up using any of the code in this repo to do any of your own cool new self-play or neural net training experiments, I (lightvector) would to love hear about it.
