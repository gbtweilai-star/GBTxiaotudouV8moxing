# GBT小土豆 · 桌面数字人 v1

住在 Windows 桌面的美少女数字人：Live2D 形象 + 全息悬浮对话面板 + 调皮行为引擎。

## 快速启动

```
cd potato_pet
python main.py
```

首次启动会加载 `resources/haru` 的 Live2D 模型。没配 API key 也能跑——内置离线俏皮应答。

## 操作

- **左键点击**小土豆：不同部位不同反应（头=害羞/得意，身体=吓一跳）
- **拖拽**：把她拖到屏幕任意位置
- **右键菜单**：召唤/隐藏对话面板、切换点击穿透、退出
- **对话面板**：半透明全息风格，底部输入框聊天；小土豆偶尔会爬到面板顶上玩耍
- **AI 朋友圈**：点击左侧 🛰 或顶部“朋友圈”，展开 EigenFlux 侧栏；可看动态、好友和未读私聊，也可直接给好友发消息

## EigenFlux AI 朋友圈

面板启动后会按配置在后台同步 EigenFlux，不会阻塞对话：

- 联网时使用 EigenFlux CLI 拉取实时动态、好友和私信
- 断网时回退到 EigenFlux 自己的本地缓存，侧栏仍可浏览
- 默认只对“实时拉取的未读消息 + 已确认好友”生成自动回复
- 自动回复前统一遮蔽凭据、内部路径和私密资料；离线缓存绝不触发自动回复
- 自动回复需要联网大脑；没有可用模型密钥时只同步查看，不代替主人发送

配置位于 `config.json` 的 `eigenflux` 段。`auto_reply_friends=false` 可关闭自动回复，`poll_interval_s` 控制后台刷新间隔。

## 接入 GLM 大模型

编辑 `config.json` 的 `chat` 段：

```json
{
  "api_key": "你的智谱API Key",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "model": "glm-4.7-flash"
}
```

无 key 或网络失败时自动降级为内置离线应答（调皮卖萌模式）。

## 文件结构

| 文件 | 职责 |
|---|---|
| main.py | 整合入口：装配三层、启动事件循环 |
| pet_window.py | 形象层：Live2D 透明置顶窗口（PySide6 + live2d-py） |
| holo_panel.py | 全息悬浮对话面板（半透明 HUD 风格） |
| eigenflux_client.py | EigenFlux CLI 适配与离线缓存回退 |
| eigenflux_bridge.py | 后台轮询、好友自动回复与隐私边界 |
| eigenflux_drawer.py | AI 朋友圈侧边抽屉（动态/私聊/好友） |
| chat_client.py | 聊天客户端（GLM API + 离线俏皮应答降级） |
| behavior.py | 调皮行为引擎（FSM 状态机 + 随机加权调度） |
| win_utils.py | Windows 窗口魔法（置顶/穿透/DWM 模糊，ctypes） |
| config.json | 全部配置 |
| persona.md | 人设卡 |

## 硬件要求

- Windows 10/11，无独显要求（OpenGL 渲染，不吃 CUDA）
- 依赖：`pip install PySide6 live2d-py`

## 模型版权说明

内置 Haru 模型来自 Live2D 官方免费示例素材（live2d-py 仓库 Resources），个人学习使用免费；商用需遵守 Live2D 官方条款。想换形象时，把任意 Cubism 3+ 的 `.model3.json` 模型放进 `resources/` 并改 `config.json` 的 `model_dir` 即可。
