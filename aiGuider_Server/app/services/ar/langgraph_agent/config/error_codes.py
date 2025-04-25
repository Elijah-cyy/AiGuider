"""
错误码定义

统一管理项目中所有错误码的模块，便于维护和扩展。
"""

import uuid
from typing import Optional

# 错误码定义
class ErrorCodes:
    """统一的错误码定义"""

    # 配置错误 (CONFIG)
    CONFIG_FILE_NOT_FOUND = "CONFIG_001"    # 配置文件不存在
    CONFIG_PARSE_ERROR = "CONFIG_002"       # 配置文件解析错误
    CONFIG_INVALID = "CONFIG_003"           # 配置无效

    # 模型错误 (MODEL)
    MODEL_CONFIG_NOT_FOUND = "MODEL_001"    # 模型配置不存在
    MODEL_DEPENDENCY_MISSING = "MODEL_002"  # 模型所需依赖缺失
    MODEL_API_KEY_MISSING = "MODEL_003"     # 模型API密钥缺失
    MODEL_INIT_FAILED = "MODEL_004"         # 模型初始化失败
    MODEL_TYPE_NOT_SUPPORTED = "MODEL_005"  # 不支持的模型类型
    MODEL_INVOKE_FAILED = "MODEL_006"       # 模型调用失败

    # API错误 (API)
    API_INVALID_REQUEST = "API_001"         # 无效的请求
    API_UNAUTHORIZED = "API_002"            # 未授权
    API_RATE_LIMIT = "API_003"              # 速率限制

    # 图错误 (GRAPH)
    GRAPH_BUILD_FAILED = "GRAPH_001"        # 图构建失败
    GRAPH_NODE_NOT_FOUND = "GRAPH_002"      # 节点不存在

    # 工具错误 (TOOL)
    TOOL_INVOKE_FAILED = "TOOL_001"         # 工具调用失败
    TOOL_NOT_FOUND = "TOOL_002"             # 工具不存在


class BaseError(Exception):
    """基础错误类"""

    def __init__(self, message: str, error_code: str, error_id: Optional[str] = None):
        """
        初始化基础错误

        Args:
            message: 错误信息
            error_code: 错误码
            error_id: 错误唯一标识，用于调试和跟踪，如不提供则自动生成
        """
        self.error_code = error_code
        self.error_id = error_id or str(uuid.uuid4())
        self.message = message
        super().__init__(f"[{error_code}] {message} (ID: {self.error_id})")

    def to_dict(self):
        """转换为字典，用于API响应"""
        return {
            "error_code": self.error_code,
            "error_id": self.error_id,
            "message": self.message
        }


class ConfigError(BaseError):
    """配置错误"""
    pass


class ModelError(BaseError):
    """模型错误"""
    pass


class ApiError(BaseError):
    """API错误"""
    pass


class GraphError(BaseError):
    """图错误"""
    pass


class ToolError(BaseError):
    """工具错误"""
    pass
