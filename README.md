# AlertWechat - Alertmanager企业微信告警转发器

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

AlertWechat 是一个基于Flask的微服务，用于接收Prometheus Alertmanager的告警并转发到企业微信群机器人。

## 功能特性

- 接收Alertmanager的Webhook告警通知
- 将告警转换为企业微信群机器人支持的Markdown格式
- 支持@指定成员或@所有人
- 自动区分触发告警和已恢复告警
- 提供健康检查接口

## 快速部署

### 1. 环境要求

- Python 3.6+
- Flask 2.0+
- requests库

### 2. 安装依赖

```bash
pip install flask requests
```

### 3. 运行服务

```bash
python app.py
```

默认监听端口为5001，可以通过环境变量修改：

```bash
export PORT=8080
python app.py
```

## API接口说明

### 健康检查接口

```
GET /health
```

响应示例：
```json
{"status": "ok"}
```

### 告警接收接口

```
POST /alert?key=YOUR_WEBHOOK_KEY[&mention=手机号1,手机号2][&mention_all=true]
```

请求参数：
- `key`: 必填，企业微信群机器人的Webhook Key
- `mention`: 选填，需要@的成员手机号，多个用逗号分隔
- `mention_all`: 选填，设置为true时@所有人

请求体：Alertmanager的原始告警JSON格式

## 使用示例

### 1. 直接调用API

```bash
curl -X POST \
  'http://localhost:5001/alert?key=your-webhook-key&mention_all=true' \
  -H 'Content-Type: application/json' \
  -d '{
    "receiver": "webhook",
    "status": "firing",
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighCPUUsage",
          "severity": "critical",
          "instance": "server1:9100"
        },
        "annotations": {
          "summary": "CPU usage is high",
          "description": "CPU usage on server1 is at 95%"
        },
        "startsAt": "2023-01-01T12:00:00Z"
      }
    ]
  }'
```

### 2. 配置Alertmanager

在Alertmanager的配置文件中添加webhook接收器：

```yaml
receivers:
- name: 'wechat-alert'
  webhook_configs:
  - url: 'http://your-alertwechat-server:5001/alert?key=your-webhook-key'
    send_resolved: true
```

## 告警消息格式

转换后的企业微信消息示例：

```
# 🚨 监控告警通知

**<font color="warning">⚠️ 1个告警触发</font>**

### 🔴 1. HighCPUUsage

**严重程度**: <font color="warning">critical</font>

**摘要**: CPU usage is high

**描述**: CPU usage on server1 is at 95%

**实例**: `server1:9100`

**开始时间**: 2023-01-01 12:00:00 UTC
```

## 高级配置

### 1. 使用Docker部署

```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY . .

RUN pip install flask requests

EXPOSE 5001
CMD ["python", "app.py"]
```

构建并运行：
```bash
docker build -t alertwechat .
docker run -d -p 5001:5001 -e PORT=5001 alertwechat
```

### 2. 生产环境部署建议

- 使用Gunicorn或uWSGI作为WSGI服务器
- 配置Nginx反向代理
- 添加认证中间件

## 常见问题

### Q: 为什么@所有人不生效？

A: 企业微信限制@所有人只能在text类型消息中使用，当有告警触发时，系统会自动转换为text消息格式。

### Q: 如何获取企业微信群机器人Webhook Key？

A: 在企业微信群聊中添加群机器人后，可以在机器人详情中获取Webhook URL，其中的key参数即为所需值。

## 贡献指南

欢迎提交Issue和Pull Request。提交代码前请确保：

1. 遵循现有代码风格
2. 更新相关文档
3. 通过基本测试

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 问题反馈

请通过GitHub Issues提交问题：  
[https://github.com/yeyoke/AlertWechat/issues](https://github.com/yeyoke/AlertWechat/issues)
