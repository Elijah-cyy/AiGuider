**方案概述:**
本方案采用 Langgraph 构建一个以名为 `thinker` 的多模态大模型节点为核心的 Agent 流程。该 Agent 遵循 ReAct (Reason-Act-Observe) 模式，处理来自 AR 眼镜的多模态输入（视觉信息、用户文本、上下文），内置安全过滤机制，并智能判断当前场景下（无论是纯图像输入还是图文混合输入）是否需要生成回复。若需回复，则通过思考、行动（调用工具）和观察（工具结果）的循环来完成任务，最终实现安全、智能且适时的导游功能。
**Langgraph 图结构设计:**
1.  **起始节点 (`start`)**: (同上)
    *   **职责**: Langgraph 图入口。
    *   **输入**: 多模态数据包。
    *   **输出**: 传递给 `thinker`。
2.  **核心思考节点 (`thinker`)**:
    *   **核心模型**: `Qwen2.5-VL`。
    *   **ReAct 角色**: 主要负责 **Reasoning (思考)** 阶段。
    *   **职责**:
        *   **初步过滤与判断 (Initial Filtering & Judgment)**:
            *   **交互意图/必要性判断**: 分析整体输入（视觉、文本、上下文、时间间隔），判断：
                *   这是否是一次明确的、需要 AI 响应的用户交互？（区分用户间对话）
                *   **对于纯图像输入或图文输入**，当前视觉场景或用户问题是否真的有意义、值得 AI 主动或被动地给出回复？（例如，避免对静态、无变化的普通场景或无意义的文本反复响应）。
            *   如果判断无需响应（非交互或场景/问题无实质内容），输出 `Ignore Signal`。
        *   **多模态理解**: 若判断需要响应，则深入理解图像和文本内容。
        *   **任务识别与规划**: 确定用户目标或主动讲解内容。
        *   **思考与行动决策 (Reason & Action Decision)**:
            *   **思考 (Thought)**: 分析完成任务所需的步骤和信息。
            *   **行动决策 (Action Decision)**: 决定是调用工具 (Action) 还是直接生成答案。
        *   **安全过滤 (Safety Filtering)**: 在生成最终答案或确定工具调用（特别是涉及生成内容的工具）之前，进行内容安全检查，过滤不当或有害信息。如果检测到不安全内容，需要中止流程返回安全提示。
        *   **输出生成**:
            *   若安全且需工具，生成 **行动指令 (Tool Call / Action)**。
            *   若安全且无需工具，生成 **最终答案 (Final Answer)**。
            *   若不安全，可能输出特定的错误/安全提示或中止信号。
            *   若在初步判断阶段决定忽略，输出 **忽略信号 (Ignore Signal)**。
    *   **输出**:
        *   行动指令 (Tool Call / Action)
        *   最终答案，包括安全提示 (Final Answer)
        *   忽略信号 (Ignore Signal)
3.  **条件路由节点 (`router`)**:
    *   **职责**: 根据 `thinker` 输出分发流程。
    *   **输入**: `thinker` 的输出。
    *   **逻辑**:
        *   `Tool Call` -> `tools`。
        *   `Final Answer` -> `end`。
        *   `Ignore Signal` -> `end` 。
4.  **工具节点 (`tools`)**: (同上)
    *   **ReAct 角色**: 执行 **Act (行动)** 。
    *   **职责**: 执行工具调用，获取结果。
    *   **输入**: `Tool Call` 指令。
5.  **结束节点 (`end`)**: (同上)
    *   **职责**: 标记流程结束。
    *   **输入**: `Final Answer`, `Ignore Signal`, 或安全信号。
    *   **处理**: 输出响应或静默结束/安全提示。