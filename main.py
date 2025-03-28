from flask import Flask, request, jsonify
import requests
import json
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 企业微信机器人webhook URL前缀，实际使用时需要拼接完整URL
WECHAT_WEBHOOK_BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key="

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok"}), 200

@app.route('/alert', methods=['POST'])
def receive_alert():
    """接收Alertmanager的告警并转发到企业微信"""
    try:
        # 获取Alertmanager发送的告警数据
        alert_data = request.json
        logger.info(f"收到告警: {json.dumps(alert_data, ensure_ascii=False)}")
        
        # 获取请求参数中的企业微信机器人key和@提及的人员
        webhook_key = request.args.get('key', '')
        mention_mobiles = request.args.get('mention', '')  # 用逗号分隔的手机号列表
        mention_all = request.args.get('mention_all', 'false').lower() == 'true'
        
        if not webhook_key:
            return jsonify({"error": "缺少企业微信机器人key参数"}), 400
        
        # 构建企业微信webhook完整URL
        webhook_url = f"{WECHAT_WEBHOOK_BASE_URL}{webhook_key}"
        
        # 转换告警格式
        wechat_message = convert_to_wechat_format(alert_data, mention_mobiles, mention_all)
        
        # 发送到企业微信
        response = requests.post(webhook_url, json=wechat_message)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info("告警已成功发送到企业微信")
                return jsonify({"status": "success", "message": "告警已发送到企业微信"}), 200
            else:
                logger.error(f"企业微信API返回错误: {result}")
                return jsonify({"status": "error", "message": f"企业微信API返回错误: {result}"}), 500
        else:
            logger.error(f"发送到企业微信失败，状态码: {response.status_code}")
            return jsonify({"status": "error", "message": f"发送到企业微信失败，状态码: {response.status_code}"}), 500
            
    except Exception as e:
        logger.exception("处理告警时发生错误")
        return jsonify({"status": "error", "message": str(e)}), 500

def convert_to_wechat_format(alert_data, mention_mobiles, mention_all=False):
    """
    将Alertmanager告警格式转换为企业微信机器人消息格式
    
    参数:
    - alert_data: Alertmanager发送的告警数据
    - mention_mobiles: 需要@的用户手机号列表，逗号分隔
    - mention_all: 是否@所有人
    
    返回:
    - 企业微信机器人消息格式的字典
    """
    # 提取告警信息
    alerts = alert_data.get('alerts', [])
    
    if not alerts:
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": "收到空告警数据"
            }
        }
    
    # 构建markdown格式的消息
    markdown_content = "# 🚨 监控告警通知\n\n"
    
    # 添加告警状态统计
    firing_count = sum(1 for alert in alerts if alert.get('status') == 'firing')
    resolved_count = sum(1 for alert in alerts if alert.get('status') == 'resolved')
    
    if firing_count > 0:
        markdown_content += f"**<font color=\"warning\">⚠️ {firing_count}个告警触发</font>**\n\n"
    
    if resolved_count > 0:
        markdown_content += f"**<font color=\"info\">✅ {resolved_count}个告警已恢复</font>**\n\n"
    
    # 处理每个告警
    for i, alert in enumerate(alerts):
        status = alert.get('status', '')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        starts_at = alert.get('startsAt', '').replace('T', ' ').replace('Z', ' UTC')
        ends_at = alert.get('endsAt', '').replace('T', ' ').replace('Z', ' UTC')
        
        # 告警状态图标
        status_icon = "🔴" if status == "firing" else "🟢"
        
        # 告警名称和严重程度
        alert_name = labels.get('alertname', '未知告警')
        severity = labels.get('severity', '未知')
        severity_color = {
            'critical': 'warning',
            'warning': 'warning',
            'info': 'info'
        }.get(severity.lower(), 'comment')
        
        markdown_content += f"### {status_icon} {i+1}. {alert_name}\n\n"
        markdown_content += f"**严重程度**: <font color=\"{severity_color}\">{severity}</font>\n\n"
        
        # 告警描述
        if 'summary' in annotations:
            markdown_content += f"**摘要**: {annotations.get('summary')}\n\n"
        
        if 'description' in annotations:
            markdown_content += f"**描述**: {annotations.get('description')}\n\n"
        
        # 告警目标
        if 'instance' in labels:
            markdown_content += f"**实例**: `{labels.get('instance')}`\n\n"
        
        if 'job' in labels:
            markdown_content += f"**任务**: `{labels.get('job')}`\n\n"
        
        # 告警时间
        if status == 'firing':
            markdown_content += f"**开始时间**: {starts_at}\n\n"
        else:
            markdown_content += f"**开始时间**: {starts_at}\n**恢复时间**: {ends_at}\n\n"
        
        # 添加分隔线
        if i < len(alerts) - 1:
            markdown_content += "---\n\n"
    
    # 构建企业微信消息
    wechat_message = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content
        }
    }
    
    # 添加@提及功能
    # 注意：企业微信的markdown消息中的@提及不会生效
    # 需要使用专门的mentioned_list或mentioned_mobile_list字段
    if mention_all:
        # 使用text类型消息，因为markdown不支持@所有人
        wechat_message = {
            "msgtype": "text",
            "text": {
                "content": f"🚨 监控告警通知\n\n{firing_count}个告警触发，{resolved_count}个告警已恢复\n\n请查看详细信息",
                "mentioned_list": ["@all"]
            }
        }
    elif mention_mobiles:
        # 分割手机号列表
        mobiles = [mobile.strip() for mobile in mention_mobiles.split(',') if mobile.strip()]
        if mobiles:
            # 对于markdown消息，添加mentioned_mobile_list
            wechat_message["markdown"]["mentioned_mobile_list"] = mobiles
    
    return wechat_message

if __name__ == '__main__':
    # 从环境变量获取端口，默认为5001
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
