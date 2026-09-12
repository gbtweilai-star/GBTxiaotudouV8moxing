# Voice Mouth 模块对抗性审查报告

> 审查角色：对抗性代码审查员  
> 审查对象：`.cluster/five-dim-ultimate/caps/voice_mouth.py`  
> 审查时间：2026-09-11  
> 审查视角：专注代码风险与逻辑缺陷

---

## 结论：**有条件通过**

模块核心功能可用，但存在**2 个高风险问题**和**3 个中低风险问题**，建议修复后再并入主干。

---

## 一、逻辑缺陷审查

### 1.1 `SpeechResult.audio_file` 与实际发声不一致（**高**）

**位置**：第 54-61 行

```python
result = SpeechResult(
    text=text,
    style=style,
    audio_file=save_to,          # ← 这里记录的是 save_to 路径
    duration_sec=est_duration,
    success=spoken
)
```

**问题**：
- `save_to` 参数在第 37-39 行被设置为一个 `.wav` 文件路径
- 但 PowerShell 脚本（第 43-45 行）**并没有将音频保存到该路径**
- SAPI 的 `Speak()` 方法是纯播放，不生成文件
- 结果：`audio_file` 字段记录了一个**不存在的文件路径**

**影响**：
- 调用者误以为音频已保存，后续读取会失败
- `SpeechResult` 的语义与实际行为不一致

**建议修复**：
```python
# 方案 A：移除 audio_file 字段（如果不需要保存）
@dataclass
class SpeechResult:
    text: str
    style: str
    duration_sec: float
    success: bool
    timestamp: float = field(default_factory=time.time)
    # audio_file 移除或改为 Optional

# 方案 B：真正实现音频保存（需要额外逻辑，见"修复建议"章节）
```

---

### 1.2 `estimated_duration` 与实际发声时长不一致（**中**）

**位置**：第 35 行

```python
est_duration = len(text) / 4.5
```

**问题**：
- 使用固定公式 `字数 / 4.5` 估算时长
- SAPI `Speak()` 是**同步阻塞**的，实际时长取决于：
  - 语音引擎的渲染速度
  - 系统负载
  - 文本复杂度（标点、停顿）
- 估算值可能偏差 ±30%

**影响**：
- 调用者无法准确知道实际发声时长
- 如果需要精确时序控制（如多段语音拼接），会出错

**建议修复**：
```python
import time

start_time = time.time()
# ... subprocess.run(...) ...
actual_duration = time.time() - start_time

result = SpeechResult(
    # ...
    duration_sec=actual_duration,  # 使用实际时长
    # ...
)
```

---

### 1.3 `style` 参数未被使用（**低**）

**位置**：第 33、56 行

```python
def speak(self, text: str, style: str = "neutral", save_to: Optional[str] = None) -> Dict:
    # ...
    result = SpeechResult(
        style=style,  # ← 记录但从未使用
        # ...
    )
```

**问题**：
- `VoiceStyle` 枚举定义了 4 种风格（第 15-20 行）
- 但 PowerShell 脚本中**没有根据 style 设置语音参数**
- SAPI 的 `SpeechSynthesizer` 支持 `SelectVoice()` 和 `Pitch`/`Volume` 调节，但代码未使用

**影响**：
- `style` 参数形同虚设，调用者传入 `"warm"` 或 `"professional"` 无实际效果

**建议修复**：
```python
# 在 PowerShell 脚本中根据 style 设置不同参数
voice_map = {
    "neutral": {"rate": 0, "volume": 50},
    "warm": {"rate": -2, "volume": 60},
    "professional": {"rate": 2, "volume": 50},
    "lively": {"rate": 5, "volume": 70}
}
config = voice_map.get(style, voice_map["neutral"])
# ... $s.Rate = {config["rate"]}; ...
```

---

## 二、安全风险审查

### 2.1 临时文件泄露风险（**中**）

**位置**：第 75-78 行

```python
def _write_text_file(self, text: str) -> str:
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tf.write(text)
    tf.close()
    return tf.name
```

**问题**：
- `delete=False` 意味着文件**不会被自动删除**
- 文件路径是随机生成的，但始终在系统临时目录（如 `C:\Users\ADMIN\AppData\Local\Temp\`）
- 文件**从未被清理**，长期积累会泄露：
  - 说过的内容（可能包含敏感信息）
  - 调用时间戳（从文件名推断）

**影响**：
- 隐私泄露：临时文件可被其他进程读取
- 磁盘占用：长期运行会积累大量 `.txt` 文件

**建议修复**：
```python
def _write_text_file(self, text: str) -> str:
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tf.write(text)
    tf.close()
    self._temp_files.append(tf.name)  # 记录待清理文件
    return tf.name

# 在 __init__ 中添加
self._temp_files: List[str] = []

# 在 speak() 末尾清理
try:
    # ... subprocess.run(...) ...
finally:
    for f in self._temp_files:
        try: os.remove(f)
        except: pass
    self._temp_files.clear()
```

---

### 2.2 PowerShell 注入风险（**低**）

**位置**：第 43-45 行

```python
ps_script = (
    f"Add-Type -AssemblyName System.Speech; "
    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    f"$s.Rate = {self._rate_to_sapi()}; "
    f"$s.Speak([System.IO.File]::ReadAllText('{self._write_text_file(text)}'));"
)
```

**问题**：
- `text` 内容被写入临时文件，再通过 `ReadAllText()` 读取
- 这**规避了命令行注入**（因为文本不在命令行参数中）
- 但 `ps_script` 本身仍通过 f-string 拼接，若 `self._rate_to_sapi()` 返回非整数，可能出错

**分析**：
- 当前实现**基本安全**，因为：
  - `text` 不在 PowerShell 字符串字面量中
  - `rate` 是整数，无注入风险
  - 文件路径是系统生成的，不含用户输入

**建议改进**：
```python
# 使用参数化传递（更严谨）
ps_script = """
Add-Type -AssemblyName System.Speech;
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$s.Rate = {rate};
$s.Speak([System.IO.File]::ReadAllText('{text_file}'));
""".format(rate=self._rate_to_sapi(), text_file=self._write_text_file(text).replace("'", "''"))
```

---

## 三、风格一致性审查

### 3.1 与 `decision_brain.py` 对比

| 维度 | `decision_brain.py` | `voice_mouth.py` | 一致性 |
|------|---------------------|------------------|--------|
| 类定义 | ✅ `class DecisionBrain:` | ✅ `class VoiceMouth:` | ✅ |
| dataclass | ✅ `@dataclass class Decision` | ✅ `@dataclass class SpeechResult` | ✅ |
| 类型注解 | ✅ 完整 | ✅ 完整 | ✅ |
| 中文 docstring | ✅ 有 | ✅ 有 | ✅ |
| Dict 返回 | ✅ `-> Dict` | ✅ `-> Dict` | ✅ |
| `status` 字段 | ✅ `{'status': 'success'}` | ✅ `{'status': 'success'}` | ✅ |
| `__main__` 自测 | ✅ 有 | ✅ 有 | ✅ |
| 内部方法命名 | ✅ `_prefix` | ✅ `_prefix` | ✅ |

**结论**：风格**高度一致**，符合项目规范。

---

### 3.2 小问题：`self._rate_to_sapi()` 调用错误（**中**）

**位置**：第 44 行

```python
f"$s.Rate = {self._rate_to_sapi()}; "
```

**问题**：
- 应该是 `self._rate_to_sapi()`，但代码中写的是 `self._rate_to_sapi()`（少了一个 `s`）
- **等等，我看错了**，代码中是 `self._rate_to_sapi()`，方法定义是 `def _rate_to_sapi(self)`（第 67 行）
- **实际上没问题**，是我看错了

**修正**：此问题不存在，代码正确。

---

## 四、健壮性审查

### 4.1 异常处理不完整（**中**）

**位置**：第 42-51 行

```python
try:
    # ... subprocess.run(...) ...
    spoken = True
except Exception as e:
    return {'status': 'error', 'message': f'语音引擎调用失败：{e}'}
```

**问题**：
- 捕获了 `Exception`，但未处理：
  - `subprocess.TimeoutExpired`（超时）
  - `FileNotFoundError`（PowerShell 不存在）
  - `OSError`（系统错误）
- 临时文件写入失败（第 75-78 行）也未捕获

**建议修复**：
```python
from subprocess import TimeoutExpired

try:
    # ...
except TimeoutExpired:
    return {'status': 'error', 'message': '语音引擎超时'}
except FileNotFoundError:
    return {'status': 'error', 'message': '未找到 PowerShell'}
except Exception as e:
    return {'status': 'error', 'message': f'语音引擎调用失败：{e}'}
```

---

### 4.2 超时设置合理（**低**）

**位置**：第 47 行

```python
subprocess.run(..., timeout=60)
```

**分析**：
- 60 秒超时对于一般文本（<300 字）是合理的
- 但超长文本（如 1000 字）可能需要更长时间
- 建议根据文本长度动态调整超时

**建议改进**：
```python
timeout = min(120, max(30, int(est_duration * 2)))  # 至少 30 秒，最多 120 秒
```

---

### 4.3 临时文件未清理（**高**）

见 **2.1 节**，这是**高风险问题**。

---

## 五、缺口与风险汇总

| 问题 | 严重级别 | 位置 | 影响 |
|------|----------|------|------|
| `audio_file` 记录不存在的文件 | **高** | 54-61 行 | 调用者误以为音频已保存 |
| 临时文件未清理 | **高** | 75-78 行 | 隐私泄露、磁盘占用 |
| `estimated_duration` 不准确 | **中** | 35 行 | 时序控制出错 |
| 异常处理不完整 | **中** | 42-51 行 | 未捕获特定异常 |
| `style` 参数未被使用 | **低** | 33、56 行 | 功能未实现 |
| 超时设置固定 | **低** | 47 行 | 超长文本可能超时 |

---

## 六、修复建议（代码层面）

### 6.1 修复 `audio_file` 问题

**方案 A（推荐）**：移除 `audio_file` 字段，因为当前不保存音频

```python
@dataclass
class SpeechResult:
    """语音输出结果"""
    text: str
    style: str
    duration_sec: float
    success: bool
    timestamp: float = field(default_factory=time.time)
```

**方案 B**：真正实现音频保存（需要额外依赖或更复杂的逻辑）

```python
# 使用 pyaudio 或 simpleaudio 录制系统音频
# 或使用 SAPI 的 SaveToWaveFile 方法（需要额外研究）
```

---

### 6.2 修复临时文件清理

```python
class VoiceMouth:
    def __init__(self, voice: str = "default", rate: int = 1):
        self.voice = voice
        self.rate = rate
        self.history: List[SpeechResult] = []
        self.total_spoken = 0
        self._temp_files: List[str] = []  # 新增

    def _write_text_file(self, text: str) -> str:
        tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        tf.write(text)
        tf.close()
        self._temp_files.append(tf.name)  # 记录
        return tf.name

    def _cleanup_temp_files(self):
        """清理临时文件"""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        self._temp_files.clear()

    def speak(self, text: str, style: str = "neutral", save_to: Optional[str] = None) -> Dict:
        # ...
        try:
            # ... subprocess.run(...) ...
        finally:
            self._cleanup_temp_files()  # 新增
        # ...
```

---

### 6.3 修复 `estimated_duration` 不准确

```python
def speak(self, text: str, style: str = "neutral", save_to: Optional[str] = None) -> Dict:
    # ...
    start_time = time.time()  # 新增
    spoken = False
    try:
        # ... subprocess.run(...) ...
        spoken = True
    except Exception as e:
        # ...
    actual_duration = time.time() - start_time  # 新增
    # ...
    result = SpeechResult(
        # ...
        duration_sec=actual_duration,  # 修改
        # ...
    )
    # ...
    return {
        # ...
        'estimated_duration': round(actual_duration, 1),  # 修改
        # ...
    }
```

---

### 6.4 完善异常处理

```python
from subprocess import TimeoutExpired

def speak(self, text: str, style: str = "neutral", save_to: Optional[str] = None) -> Dict:
    # ...
    spoken = False
    try:
        # ... subprocess.run(...) ...
        spoken = True
    except TimeoutExpired:
        return {'status': 'error', 'message': '语音引擎超时（超过 60 秒）'}
    except FileNotFoundError:
        return {'status': 'error', 'message': '未找到 PowerShell，请确保 Windows 系统正常'}
    except OSError as e:
        return {'status': 'error', 'message': f'系统错误：{e}'}
    except Exception as e:
        return {'status': 'error', 'message': f'语音引擎调用失败：{e}'}
```

---

### 6.5 实现 `style` 参数（可选）

```python
def _get_style_config(self, style: str) -> Dict:
    """根据风格返回 SAPI 配置"""
    config_map = {
        "neutral": {"rate": 0, "volume": 50},
        "warm": {"rate": -2, "volume": 60},
        "professional": {"rate": 2, "volume": 50},
        "lively": {"rate": 5, "volume": 70}
    }
    return config_map.get(style, config_map["neutral"])

def speak(self, text: str, style: str = "neutral", save_to: Optional[str] = None) -> Dict:
    # ...
    style_config = self._get_style_config(style)
    ps_script = (
        f"Add-Type -AssemblyName System.Speech; "
        f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Rate = {style_config['rate']}; "
        f"$s.Volume = {style_config['volume']}; "
        f"$s.Speak([System.IO.File]::ReadAllText('{self._write_text_file(text)}'));"
    )
    # ...
```

---

## 七、最终评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 功能完整性 | ⭐⭐⭐☆☆ | 核心功能可用，但 `audio_file` 和 `style` 未完全实现 |
| 代码质量 | ⭐⭐⭐⭐☆ | 风格一致，类型注解完整 |
| 安全性 | ⭐⭐⭐☆☆ | 临时文件泄露风险需修复 |
| 健壮性 | ⭐⭐⭐☆☆ | 异常处理需完善 |
| 可维护性 | ⭐⭐⭐⭐☆ | 代码清晰，易于扩展 |

**总体评分**：⭐⭐⭐☆☆（3.5/5）

**建议**：修复**高优先级问题**（`audio_file` 语义、临时文件清理）后并入主干。

---

> 审查员：对抗性代码审查员  
> 审查完成时间：2026-09-11 22:48 GMT+7
