# glibc-all-in-one

[English](README_EN.md)

**pwn 选手的 glibc 瑞士军刀。** 智能识别参数，不记 flag，拿来就用。下载、搜索、识别、比对、编译——覆盖 pwn 场景下 glibc 的全生命周期。

> 旧版 shell 脚本已移至 [`legacy/`](legacy/README.md)，不再维护。`glibc-aio` 是全新 v2 重写。

## Install

```bash
git clone https://github.com/matrix1001/glibc-all-in-one.git
cd glibc-all-in-one
pip install -e .
```

Python 3.10+。`pip install` 自动安装 `pyelftools`（ELF 解析）和 `zstandard`（.deb zstd 解压），无其他依赖。

首次使用需要拉取可用包列表（约需 5 秒，生成 `list` 文件）：

```bash
$ glibc-aio mirror update
[+] Saved 32 + 48 old packages to "list"
```

## Quick Start

三条命令覆盖 pwn 最常见的场景：

```bash
# 1. 泄露地址 → 反查 libc 版本
$ glibc-aio puts 0x80970 system 0x4f440
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64          ← 精准命中

# 2. 下载 + 查看符号
$ glibc-aio download 2.27-3ubuntu1_amd64
[+] Downloaded to libs/2.27-3ubuntu1_amd64

$ glibc-aio 2.27 system                ← 版本号 + 符号名，自动搜本地已下载的 libc
2.27-3ubuntu1_amd64:
  000000000004f440  STT_FUNC  system

# 3. 识别未知 libc
$ glibc-aio ./unknown-libc.so
Method:    buildid
Version:   2.27-3ubuntu1.5_amd64
BuildID:   4176c5eec6b8c6e04aa1eae2cd4b76b1
```

## Command Reference

### 子命令（精确控制）

| 命令 | 说明 |
|------|------|
| `glibc-aio mirror list` | 显示 4 个镜像源及类型（regular / fallback） |
| `glibc-aio mirror update` | 从所有镜像拉取可用包列表，写入 `list` 文件 |
| `glibc-aio search 2.35` | 按包名模糊搜索可用版本 |
| `glibc-aio search --symbol system=0x4f440` | 按符号偏移反查 libc 版本（libc.rip 在线） |
| `glibc-aio search --symbol a=0x1 --symbol b=0x2` | 多符号 AND 查询 |
| `glibc-aio search --symbol ... --tol 5` | 偏移容差 ±N 字节 |
| `glibc-aio search --buildid abc123` | 按 BuildID 查找 |
| `glibc-aio search --libc ./libc.so --symbol system` | 在指定 libc 文件中查找符号 |
| `glibc-aio search --libc ./libc.so --symbol "*exec*"` | glob 匹配符号名 |
| `glibc-aio search --libc ./libc.so --ends-with f30` | 地址末位匹配（partial overwrite 神器） |
| `glibc-aio search --libc ./libc.so --str "/bin/sh"` | 在 .rodata/.data 中搜字符串，返回偏移 |
| `glibc-aio download 2.27-3ubuntu1_amd64` | 下载 libc + debug symbols |
| `glibc-aio download <id> --mirror tuna` | 指定镜像 |
| `glibc-aio download <id> --no-dbg` | 跳过 debug symbols |
| `glibc-aio download <id> --keep-deb` | 保留 .deb 文件不删除 |
| `glibc-aio identify ./libc.so` | BuildID 在线 → 符号指纹本地，双路识别版本 |
| `glibc-aio identify --offline ./libc.so` | 仅本地符号指纹，不联网 |
| `glibc-aio diff libc-a.so libc-b.so` | 比对两个 libc：符号增删、偏移变化、安全属性差异 |
| `glibc-aio build 2.29 amd64` | Docker 容器编译（版本→镜像自动映射） |
| `glibc-aio build 2.27 i686` | 32 位交叉编译 |
| `glibc-aio build ... --image ubuntu:16.04` | 指定 Docker 镜像 |
| `glibc-aio build ... --no-docker` | 宿主机直接编译 |

所有子命令支持 `--json` 输出。

### 智能分发（不需要子命令）

不敲子命令时，`glibc-aio` 根据参数类型自动判断意图：

| 输入 | 自动执行 | 示例输出 |
|------|---------|----------|
| `glibc-aio 2.35` | 搜可用包 | `2.35-0ubuntu3.13_amd64  2.35-0ubuntu3_amd64 ...` |
| `glibc-aio 2.27 system` | 已下载 libc 中查符号 | `2.27-3ubuntu1_amd64:  000000000004f440  system` |
| `glibc-aio 2.35 "*mmap*"` | 已下载 libc 中 glob 搜 | 列出所有匹配版本的 mmap 偏移 |
| `glibc-aio system 0x4f440` | 在线反查版本 | `[Online] libc6_2.27-3ubuntu1.5_amd64` |
| `glibc-aio puts 0x80970 system 0x4f440` | 多符号 AND | 同时满足两个偏移的 libc 版本 |
| `glibc-aio ./libc.so` | 识别版本 | `Method: buildid  Version: 2.27-3ubuntu1.5_amd64` |
| `glibc-aio ./libc.so system` | 查符号偏移 | `000000000004f440  STT_FUNC  system` |
| `glibc-aio ./libc.so "*exec*"` | glob 搜符号 | 14 个匹配符号（execl, execv, execve...） |
| `glibc-aio ./libc.so 0xf30` | 末位匹配（3 hex digits = 12-bit mask） | 匹配 `f30` 的 7 个符号 |
| `glibc-aio ./libc.so 0x80` | 末位匹配（2 hex digits = 1 byte） | 末字节 `80` 的符号 |
| `glibc-aio ./libc.so system 0x380` | 符号 + 末位组合 | 先 glob 再末位过滤 |

**智能分发规则：** 存在的文件路径 → libc 文件；`0x` 开头或 ≥5 位纯 hex → 地址；`数字.数字` → 版本号；其余 → 符号名。参数在前文是文件时，后续 hex 不限制长度（`0x80`、`f30` 均可）。

## 详细用法

### `search` — 查版本 / 搜 libc

```bash
# 在线 — 包名模糊搜
$ glibc-aio search 2.35
2.35-0ubuntu3.13_amd64
2.35-0ubuntu3_amd64
[*] 4 result(s)

# 在线 — 单个符号反查版本
$ glibc-aio search --symbol system=0x4f440
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64
  libc6_2.27-0ubuntu2_amd64
  ...

# 在线 — 多符号 AND + 容差
$ glibc-aio search --symbol puts=0x80970 --symbol system=0x4f440 --tol 5
[Online (libc.rip)]
  libc6_2.27-3ubuntu1.5_amd64
[Local symdb]                                   ← 本地已下载的也会被搜
  libc6_2.27-3ubuntu1_amd64  (2 symbol(s) matched)

# 在线 — BuildID
$ glibc-aio search --buildid 4176c5eec6b8c6e04aa1eae2cd4b76b1

# 本地 — 查符号
$ glibc-aio search --libc ./libc.so --symbol system
000000000004f440  STT_FUNC  system

# 本地 — glob
$ glibc-aio search --libc ./libc.so --symbol "*exec*"
00000000000cbfa0  STT_FUNC  execl
00000000000cbde0  STT_FUNC  execv
...
[*] 14 symbol(s)

# 本地 — 地址末位匹配
$ glibc-aio search --libc ./libc.so --ends-with f30
00000000000abf30  STT_FUNC  wcpncpy
000000000004f430  STT_FUNC  __libc_system
[*] 7 symbol(s)

# 本地 — 符号+末位组合
$ glibc-aio search --libc ./libc.so --symbol "*exec*" --ends-with fa0
00000000000cbfa0  STT_FUNC  execl
[*] 1 symbol(s)

# 本地 — 字符串搜索（精准扫 .rodata/.data 段，不是全文件 strings）
$ glibc-aio search --libc ./libc.so --str "/bin/sh"
  0x001b3e9a  /bin/sh
[*] 1 match(es)
```

在线模式同时查询 libc.rip API 和本地符号索引数据库。网络不可用时本地结果不受影响。本地索引在每次下载时自动建立。

### `download` — 下载 libc + debug symbols

4 个镜像源按序尝试：tuna → ustc → ubuntu-archive → old-releases（fallback）。任一下载成功即停止，对用户透明。

下载完成后自动：解压 `.deb`（支持 xz / gz / zstd 三种压缩）、提取符号建本地索引（供 `search` 和 `identify` 离线使用）、清理临时文件。

```bash
$ glibc-aio download 2.27-3ubuntu1_amd64
[+] Downloaded to libs/2.27-3ubuntu1_amd64
$ ls libs/2.27-3ubuntu1_amd64/
x86_64-linux-gnu/  .debug/                            ← libc 文件 + debug symbols

# 选项
$ glibc-aio download 2.35-0ubuntu3_amd64 --mirror tuna    # 只用指定镜像
$ glibc-aio download 2.35-0ubuntu3_amd64 --keep-deb        # 保留 .deb
$ glibc-aio download 2.31-0ubuntu9_i386 --no-dbg            # 只要 libc，不要 debug
```

### `identify` — 识别未知 libc 版本

双路 fallback。优先从 ELF 的 `.note.gnu.build-id` 提取 BuildID 在线查 libc.rip；失败则计算符号表哈希指纹在本地数据库中匹配。本地数据库随每次 `download` 自动增长。

```bash
$ glibc-aio identify ./libc.so
Method:    buildid
Version:   2.27-3ubuntu1.5_amd64
BuildID:   4176c5eec6b8c6e04aa1eae2cd4b76b1

$ glibc-aio identify --offline ./libc.so          # 不联网，仅本地指纹
Method:    fingerprint
Version:   2.27-3ubuntu1_amd64
```

### `diff` — 比对两个 libc 版本

对比符号表（新增/移除/偏移变化）和安全属性（RELRO/NX/Canary/PIE/RUNPATH）。

```bash
$ glibc-aio diff libs/2.27/libc.so libs/2.35/libc.so.6
--- libs/2.27/libc.so
+++ libs/2.35/libc.so.6
+ 000000000012e3f0 STT_FUNC STB_GLOBAL posix_spawn_file_actions_addtcsetpgrp_np
- 0000000000091d40 STT_FUNC STB_GLOBAL __strspn_c1
~ system: 0x4f440 -> 0x50d60                        ← 偏移变化
~ puts: 0x80970 -> 0x80ed0
! relro: full -> partial                            ← 安全属性退化
```

### `build` — 从源码编译 glibc

默认在 Docker 容器中编译，自动根据版本号选择 Ubuntu 镜像（2.19→14.04, 2.23-2.27→16.04, 2.28-2.29→18.04, 2.30-2.34→20.04, 2.35+→22.04）。编译产物写入 `libs/build/<version>/<arch>/`。Docker 不可用时自动回退宿主机编译。

```bash
$ glibc-aio build 2.29 amd64                     # Docker ubuntu:18.04 容器内编译
$ glibc-aio build 2.27 i686                       # 32 位交叉编译
$ glibc-aio build 2.35 amd64 --no-docker          # 宿主机直接编译
$ glibc-aio build ... --prefix /opt/glibc         # 自定义安装路径
```

### `mirror` — 镜像源管理

```bash
$ glibc-aio mirror list
  tuna                 https://mirror.tuna.tsinghua.edu.cn/... [regular]
  ustc                 https://mirrors.ustc.edu.cn/...         [regular]
  ubuntu-archive       http://archive.ubuntu.com/...           [regular]
  old-releases         http://old-releases.ubuntu.com/...      [fallback]

$ glibc-aio mirror update
[+] Saved 32 + 48 old packages to "list"           ← 统一文件，[old] 标记区分
```

## JSON

所有命令支持 `--json`，输出合法 JSON 可直接管道给 `jq`：

```bash
$ glibc-aio ./libc.so system --json | jq '.[0].addr'
"0x45380"

$ glibc-aio identify ./libc.so --json | jq -r '.id'
2.27-3ubuntu1_amd64

$ glibc-aio mirror list --json | jq '.[].name'
tuna
ustc
ubuntu-archive
old-releases
```

## 规模

| 项 | 值 |
|---|-----|
| Python | 3.10+ |
| 依赖 | `pyelftools` + `zstandard`（2 个） |
| 测试 | 28 passed |
| 命令 | 6 子命令 + 11 种智能分发 |
| 镜像 | 4（tuna / ustc / ubuntu-archive / old-releases） |
| 在线 API | libc.rip |
| 本地缓存 | `~/.cache/glibc-aio/`（符号索引 + 指纹库） |
| .deb 压缩 | xz / gz / zstd 自动检测 |

## Legacy

旧版 shell 脚本在 [`legacy/`](legacy/README.md)，保留但不维护。

```
update_list  → mirror update               list+old_list 合并为统一 list 文件
download     → download（统一入口）         不再区分 download/download_old
download_old → 自动 fallback 到 old-releases
extract      → 内建纯 Python（ar+tarfile+zstd）
build        → Docker 容器化编译
```
