# 🎓 超星学习通 · 智能刷课助手

基于 **DrissionPage** 的零风险自动刷课脚本，集成 **DeepSeek AI** 自动答题。支持 GUI 界面操作，简单易用。

## 🛡️ 安全特性

| 特性 | 说明 |
|------|------|
| **无 WebDriver 指纹** | DrissionPage 接管真实浏览器，无自动化痕迹 |
| **原生心跳上报** | 不模拟心跳包，由页面 JS 自然上报 |
| **1 倍速播放** | 固定 1 倍速，服务器无法区分 |
| **可见性伪装** | 覆盖 Page Visibility API |
| **智能调度** | 模拟人类作息，自动休息 |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd webclass-helper
pip install -r requirements.txt
```

### 2. 运行界面 (推荐)

直接运行 `gui.py` 即可打开可视化操作界面：

```bash
python gui.py
```

在界面中您可以：
- 🔑 输入账号密码并**自动保存**，下次打开无需重复输入。
- 🔍 自动检测所有在读课程，并勾选需要刷课的目标。
- ⚙️ 在界面直接配置 DeepSeek API Key 和学习时段。
- 📊 实时查看学习进度和详细日志。

### 3. 命令行运行

编辑 `config.py`，填写账号信息后运行：

```bash
python main.py
```

## 📁 项目结构

```
.
├── gui.py                  # 可视化界面入口（推荐使用）
├── main.py                 # 命令行入口
├── config.py               # 配置文件
├── core/
│   ├── browser.py          # 浏览器管理
│   ├── login.py            # 自动登录
│   ├── course.py           # 课程导航
│   ├── player.py           # 视频播放（核心）
│   ├── answer.py           # AI 答题
│   └── anti_detect.py      # 反检测
├── scheduler/
│   └── human_scheduler.py  # 智能调度
├── utils/
│   ├── logger.py           # 日志系统
│   └── random_delay.py     # 随机延迟
├── requirements.txt
└── .env.example            # 环境变量示例
```

## ⚠️ 注意事项

1. **首次运行** 可能需要手动完成滑块验证码（之后 Cookie 自动保存）
2. **保持浏览器窗口可见**（可以被遮挡但不要最小化）
3. **不要同时在手机上播放同一课程的视频**
4. 按 `Ctrl+C` 或点击界面 `STOP` 可安全退出
5. **严禁** 用于商业用途，仅供学习交流使用
