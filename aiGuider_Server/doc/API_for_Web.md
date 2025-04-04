# WEB应用的API文档说明

## 1. GET http://localhost:8000/api/v1/health/
### 路由注册
- 基础路径：/api/v1 (来自 `aiGuider_Server\app\core\config.py` 中的 API_V1_STR)
- 健康检查前缀：/health
- 组合路径：/api/v1/health/

### 请求处理流程
1. 请求路由匹配
   - 请求 GET /api/v1/health/ →
   - 匹配 api_router.include_router(health.router, prefix="/health") (位于 `app/api/api.py`)
   - 最终路由到 health_check 函数 (位于 `app/api/endpoints/health.py`)
2. 参数解析
   - 解析请求头、查询参数和请求体
3. 业务逻辑处理
   - 执行健康检查逻辑
   - 检查数据库连接状态
4. 响应生成
   - 构造HealthResponse对象
   - 序列化为JSON格式返回

### 用途
- 监控系统健康状态
- 返回API和数据库连接状态

## 2. GET http://localhost:8000/api/v1/messages
### 路由注册
- 基础路径：/api/v1 (来自 `aiGuider_Server\app\core\config.py` 中的 API_V1_STR)
- 直接注册：/messages
- 组合路径：/api/v1/messages

### 请求处理流程
1. 请求路由匹配
   - 请求 GET /api/v1/messages →
   - 匹配 api_router.include_router(chat.router) (位于 `app/api/api.py`)
   - 最终路由到 get_messages 函数 (位于 `app/api/endpoints/chat.py`)
2. 会话验证
   - 从Cookie或Header中提取会话ID
   - 通过session_manager验证会话有效性
3. 消息获取
   - 调用session_manager.get_pending_messages()获取待处理消息
   - 消息来自session_service中的pending_messages队列
4. 响应生成
   - 构造MessagesResponse对象 (定义于 `app/api/endpoints/chat.py`)
   - 序列化为JSON格式返回

### 用途
- 获取AI主动生成的消息
- 用于实现主动交互功能
- 返回格式为MessagesResponse，包含消息列表

