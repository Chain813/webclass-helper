<div align="center">

# WebClass Helper

> OCS (Online Course Script) 网课助手 - 帮助大学生自动化完成在线课程任务

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18-green)](https://nodejs.org/)
[![pnpm](https://img.shields.io/badge/pnpm-workspace-yellow)](https://pnpm.io/)

</div>

## 简介

WebClass Helper 是一个油猴脚本（Tampermonkey/Scriptcat），支持多个在线学习平台的自动化操作，包括视频播放、题目作答等功能。

### 支持平台

| 平台 | 说明 |
|------|------|
| **ZHS** (智慧树) | 智慧树在线教育 |
| **CX** (超星) | 超星学习通 |
| **ICVE** (职教云) | 职教云 MOOC |
| **ZJY** (浙江甬工) | 浙江甬工在线 |
| **ICourse** (爱课程) | 中国大学 MOOC |
| **YKT** (雨课堂) | 雨课堂 |

### 主要功能

- 自动播放视频课程
- 基于题库的自动答题
- DeepSeek AI 智能答题
- 超星字体反混淆破解
- 多平台统一管理界面

## 项目结构

```
webclass-helper/
├── packages/
│   ├── core/           # @ocsjs/core - 核心库
│   │   └── src/
│   │       ├── answer-wrapper/  # 答案解析
│   │       ├── worker/          # 任务执行器
│   │       └── utils/           # 工具函数
│   └── scripts/        # @ocsjs/scripts - 平台脚本
│       └── src/
│           ├── projects/        # 各平台实现
│           ├── elements/        # UI 组件
│           └── utils/           # 脚本工具
├── scripts/            # 构建工具 (Gulp)
├── eslint.config.js    # ESLint 配置
└── package.json
```

## 开发

### 环境要求

- Node.js >= 18
- pnpm >= 8

### 安装依赖

```bash
pnpm install
```

### 常用命令

```bash
# 开发模式（监听文件变化）
pnpm dev

# 代码检查与格式化
pnpm lint

# TypeScript 编译
pnpm tsc

# 生产构建
pnpm build
```

### 代码规范

- 使用 ESLint + Prettier 进行代码格式化
- TypeScript 严格模式
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范

## 许可证

[MIT](LICENSE)

## 致谢

本项目基于 [ocsjs/ocsjs](https://github.com/ocsjs/ocsjs) 开发，感谢原作者 [enncy](https://github.com/enncy) 的贡献。
