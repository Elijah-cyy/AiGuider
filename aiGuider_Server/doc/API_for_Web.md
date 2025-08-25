# WEB应用的API文档说明

## 1. GET http://localhost:6160/api/v1/health/
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

## 2. GET http://localhost:6160/api/v1/messages
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
   - 消息来自session服务中的AIApplication实例的pending_messages队列
4. 响应生成
   - 构造MessagesResponse对象 (定义于 `app/api/endpoints/chat.py`)
   - 序列化为JSON格式返回

### 用途
- 获取AI主动生成的消息
- 用于实现主动交互功能
- 返回格式为MessagesResponse，包含消息列表

## 3. POST http://localhost:6160/api/v1/chat
### 路由注册
- 基础路径：/api/v1 (来自 `aiGuider_Server\app\core\config.py` 中的 API_V1_STR)
- 直接注册：/chat
- 组合路径：/api/v1/chat

### 请求处理流程
1. 请求路由匹配
   - 请求 POST /api/v1/chat →
   - 匹配 api_router.include_router(chat.router) (位于 `app/api/api.py`)
   - 最终路由到 chat 函数 (位于 `app/api/endpoints/chat.py`)
2. 会话管理
   - 从Cookie或Header中提取会话ID
   - 如果未提供会话ID，自动创建新会话
3. 参数处理
   - 解析文本消息和可选图片
   - 解析对话历史记录
   - 验证请求内容（至少提供文本或图片）
4. 业务逻辑处理
   - 调用session_manager.process_query()处理用户请求
   - 生成AI回复
5. 响应生成
   - 构造ChatResponse对象
   - 序列化为JSON格式返回

### 请求参数
- `message`: 文本消息 (Form字段，可选)
- `image`: 上传图片 (File字段，可选)
- `conversation_history`: 对话历史 (Form字段，JSON格式字符串)
- `session_id`: 会话ID (Cookie，可选)
- `X-Session-ID`: 会话ID (Header，可选，优先级高于Cookie)

### 用途
- 发送用户查询并获取AI回复
- 支持文本+图片多模态查询
- 维护会话状态和对话历史
- 返回格式为ChatResponse，包含AI回复和会话ID

## 4. （不重要）GET http://localhost:6160/
### 路由注册
- 直接在主应用上注册
- 不需要前缀
- 完整路径：/

### 请求处理流程
1. 请求路由匹配
   - 请求 GET / →
   - 匹配 @app.get("/") (位于 `app/main.py`)
   - 直接在FastAPI的主应用实例上注册，而不是通过router
2. 响应生成
   - 返回包含欢迎信息的JSON对象

### 用途
- 提供系统欢迎信息
- 作为API服务的入口点
- 可用于简单的服务可用性验证

## 5. 已定义但暂未使用的API

以下API接口已在代码中定义，但当前版本的临时前端应用未使用：

- `GET /api/v1/session/status` - 获取会话状态接口
- `POST /api/v1/guide/query` - AR导游查询接口

这些接口预留用于未来功能扩展和与AR眼镜客户端的集成。

