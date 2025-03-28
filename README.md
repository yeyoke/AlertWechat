# Alertmanager 转企业微信告警服务

## 简介

这是一个将 Prometheus Alertmanager 告警消息转换为企业微信群机器人消息格式的服务。该服务接收 Alertmanager 发送的 webhook 告警，将其转换为企业微信支持的格式，并转发到指定的企业微信群机器人。

## 功能特点

- 接收 Alertmanager webhook 告警
- 将告警信息转换为企业微信支持的 markdown 格式
- 支持通过 URL 参数指定企业微信机器人的 webhook key
- 支持@指定用户（通过手机号）
- 支持@所有人功能
- 提供健康检查接口
- 完善的日志记录和错误处理

## 安装与部署

### 前提条件

- Python 3.6+
- pip 包管理器

### 安装依赖
