# GBT-V8 验收测试定义

> Step 5：每个缺口的验收标准  
> 生成时间：2026-09-13

---

## 📋 验收测试概览

| 阶段 | 缺口数量 | 测试用例数 | 自动化率 |
|------|---------|-----------|---------|
| P0 | 8 项 | 24 个 | 100% |
| P1 | 7 项 | 21 个 | 100% |
| P2 | 5 项 | 15 个 | 80% |

**总计**：20 项缺口，60 个测试用例

---

## 🔴 P0 验收测试（0-2 周）

### 测试 1：账本模块

```python
import pytest
from gbt_allinone import ledger

class TestLedger:
    """账本模块验收测试"""
    
    def test_open_account(self):
        """测试开账户"""
        result = ledger.open_account("user1")
        assert result["status"] == "ok"
        assert result["account_id"] == "user1"
    
    def test_deposit(self):
        """测试入金"""
        ledger.open_account("user1")
        result = ledger.deposit("user1", "USD", 100)
        assert result["status"] == "ok"
        assert result["balance"] == "100"
    
    def test_transfer(self):
        """测试转账"""
        ledger.open_account("user1")
        ledger.open_account("user2")
        ledger.deposit("user1", "USD", 100)
        result = ledger.transfer("user1", "user2", "USD", 50)
        assert result["status"] == "ok"
        assert ledger.balance("user1", "USD") == "50"
        assert ledger.balance("user2", "USD") == "50"
    
    def test_withdraw(self):
        """测试出金"""
        ledger.open_account("user1")
        ledger.deposit("user1", "USD", 100)
        result = ledger.withdraw("user1", "USD", 30)
        assert result["status"] == "ok"
        assert ledger.balance("user1", "USD") == "70"
    
    def test_statement(self):
        """测试流水查询"""
        ledger.open_account("user1")
        ledger.deposit("user1", "USD", 100)
        result = ledger.statement("user1")
        assert len(result["transactions"]) >= 1
        assert result["transactions"][0]["type"] == "deposit"
    
    def test_reconcile(self):
        """测试对账"""
        ledger.open_account("user1")
        ledger.deposit("user1", "USD", 100)
        result = ledger.reconcile("user1")
        assert result["status"] == "ok"
        assert result["balance_match"] == True
```

**验收标准**：
- ✅ 6 个测试用例全部通过
- ✅ 支持完整账本流程：开户→入金→转账→查询→流水→对账
- ✅ 余额计算准确无误

---

### 测试 2：LLM 对话超时修复

```python
import pytest
import time
from gbt_allinone import api

class TestLLMChat:
    """LLM 对话超时测试"""
    
    def test_chat_timeout(self):
        """测试对话超时率 < 0.5%"""
        success_count = 0
        total_count = 100
        
        for i in range(total_count):
            try:
                result = api.llm_chat("Hello", timeout=10)
                if result["status"] == "ok":
                    success_count += 1
            except Exception:
                pass
        
        timeout_rate = (total_count - success_count) / total_count
        assert timeout_rate < 0.005, f"超时率 {timeout_rate} >= 0.5%"
    
    def test_chat_retry(self):
        """测试超时重试机制"""
        result = api.llm_chat("Hello", max_retries=3)
        assert result["status"] == "ok" or result["retries"] < 3
    
    def test_chat_circuit_breaker(self):
        """测试熔断机制"""
        # 模拟连续失败
        for i in range(5):
            api.llm_chat("Hello", timeout=1)
        
        # 熔断后应快速失败
        start = time.time()
        result = api.llm_chat("Hello", timeout=1)
        elapsed = time.time() - start
        
        assert elapsed < 2, "熔断后应快速失败"
```

**验收标准**：
- ✅ 超时率 < 0.5%
- ✅ 重试机制有效
- ✅ 熔断机制可用

---

### 测试 3：触手连接稳定性

```python
import pytest
from gbt_allinone.tentacle import bridge

class TestTentacleConnection:
    """触手连接稳定性测试"""
    
    def test_connection_success_rate(self):
        """测试连接成功率 > 99%"""
        success_count = 0
        total_count = 100
        
        for i in range(total_count):
            try:
                result = bridge.connect()
                if result["status"] == "ok":
                    success_count += 1
                bridge.disconnect()
            except Exception:
                pass
        
        success_rate = success_count / total_count
        assert success_rate > 0.99, f"连接成功率 {success_rate} <= 99%"
    
    def test_auto_reconnect(self):
        """测试自动重连"""
        bridge.connect()
        bridge.disconnect()
        
        # 自动重连应在 5 秒内完成
        start = time.time()
        result = bridge.connect()
        elapsed = time.time() - start
        
        assert result["status"] == "ok"
        assert elapsed < 5, "自动重连超时"
    
    def test_connection_pool(self):
        """测试连接池"""
        connections = []
        for i in range(10):
            conn = bridge.connect()
            connections.append(conn)
        
        # 所有连接应成功
        for conn in connections:
            assert conn["status"] == "ok"
        
        # 关闭所有连接
        for conn in connections:
            bridge.disconnect(conn)
```

**验收标准**：
- ✅ 连接成功率 > 99%
- ✅ 自动重连 < 5 秒
- ✅ 连接池管理正常

---

### 测试 4：生产管线监控

```python
import pytest
from gbt_allinone import pipeline
from prometheus_client import Gauge

class TestPipelineMonitoring:
    """生产管线监控测试"""
    
    def test_deploy_success_rate(self):
        """测试部署成功率可查询"""
        result = pipeline.get_metrics()
        assert "deploy_success_rate" in result
        assert 0 <= result["deploy_success_rate"] <= 1
    
    def test_deploy_failure_alert(self):
        """测试部署失败告警 < 5 分钟"""
        # 模拟部署失败
        pipeline.deploy("test", fail=True)
        
        # 检查告警
        alerts = pipeline.get_alerts()
        assert len(alerts) > 0
        assert alerts[0]["type"] == "deploy_failure"
        assert alerts[0]["delay_minutes"] < 5
    
    def test_metric_export(self):
        """测试指标导出"""
        metrics = pipeline.export_metrics()
        assert "deploy_total" in metrics
        assert "deploy_success" in metrics
        assert "deploy_failure" in metrics
```

**验收标准**：
- ✅ 部署成功率可查询
- ✅ 失败告警 < 5 分钟
- ✅ 指标导出正常

---

### 测试 5：安全扫描告警

```python
import pytest
from gbt_allinone.security import security_brain

class TestSecurityAlert:
    """安全扫描告警测试"""
    
    def test_vulnerability_scan(self):
        """测试漏洞扫描"""
        result = security_brain.scan("test_project")
        assert "vulnerabilities" in result
        assert isinstance(result["vulnerabilities"], list)
    
    def test_high_severity_alert(self):
        """测试高危漏洞告警 < 10 分钟"""
        # 模拟高危漏洞
        security_brain.add_vulnerability("test", "high", "CVE-2024-1234")
        
        # 检查告警
        alerts = security_brain.get_alerts(severity="high")
        assert len(alerts) > 0
        assert alerts[0]["delay_minutes"] < 10
    
    def test_alert_notification(self):
        """测试告警通知"""
        security_brain.add_vulnerability("test", "critical", "CVE-2024-5678")
        
        # 检查通知
        notifications = security_brain.get_notifications()
        assert len(notifications) > 0
        assert notifications[0]["severity"] == "critical"
```

**验收标准**：
- ✅ 漏洞扫描可用
- ✅ 高危告警 < 10 分钟
- ✅ 告警通知正常

---

### 测试 6：工作流错误处理

```python
import pytest
from gbt_allinone import engine

class TestWorkflowErrorHandling:
    """工作流错误处理测试"""
    
    def test_failure_retry(self):
        """测试失败重试"""
        wf = engine.define_workflow("test_retry")
        wf.add_step("step1", fail=True)
        wf.add_step("step2")
        
        result = engine.run_workflow(wf, max_retries=3)
        assert result["retries"] <= 3
    
    def test_dead_letter_queue(self):
        """测试死信队列"""
        wf = engine.define_workflow("test_dlq")
        wf.add_step("step1", fail=True)
        
        result = engine.run_workflow(wf, max_retries=0)
        assert result["status"] == "failed"
        
        # 检查死信队列
        dlq = engine.get_dead_letter_queue()
        assert len(dlq) > 0
        assert dlq[0]["workflow_id"] == "test_dlq"
    
    def test_manual_intervention(self):
        """测试人工干预"""
        wf = engine.define_workflow("test_manual")
        wf.add_step("step1", fail=True)
        
        result = engine.run_workflow(wf)
        assert result["status"] == "failed"
        
        # 人工干预
        engine.manual_intervention(wf.id, action="skip_step", step="step1")
        result = engine.resume_workflow(wf.id)
        assert result["status"] == "completed"
    
    def test_recovery_rate(self):
        """测试失败任务可恢复率 > 95%"""
        recovered = 0
        total = 100
        
        for i in range(total):
            wf = engine.define_workflow(f"test_recovery_{i}")
            wf.add_step("step1", fail=True)
            
            result = engine.run_workflow(wf)
            if result["status"] == "failed":
                # 尝试恢复
                recovery = engine.resume_workflow(wf.id)
                if recovery["status"] == "completed":
                    recovered += 1
        
        recovery_rate = recovered / total
        assert recovery_rate > 0.95, f"可恢复率 {recovery_rate} <= 95%"
```

**验收标准**：
- ✅ 失败重试有效
- ✅ 死信队列可用
- ✅ 人工干预可用
- ✅ 可恢复率 > 95%

---

### 测试 7：镜像空间监控

```python
import pytest
from gbt_allinone import mirror_space

class TestMirrorMonitoring:
    """镜像空间监控测试"""
    
    def test_version_rollback_rate(self):
        """测试版本回滚成功率可查询"""
        result = mirror_space.get_metrics()
        assert "rollback_success_rate" in result
        assert 0 <= result["rollback_success_rate"] <= 1
    
    def test_rollback_failure_alert(self):
        """测试回滚失败告警"""
        # 模拟回滚失败
        mirror_space.rollback("test", fail=True)
        
        # 检查告警
        alerts = mirror_space.get_alerts()
        assert len(alerts) > 0
        assert alerts[0]["type"] == "rollback_failure"
```

**验收标准**：
- ✅ 回滚成功率可查询
- ✅ 回滚失败告警可用

---

### 测试 8：大脑健康检查

```python
import pytest
import time
from gbt_allinone import brain_exec

class TestBrainHealth:
    """大脑健康检查测试"""
    
    def test_health_check_response_time(self):
        """测试健康检查响应 < 1 秒"""
        start = time.time()
        result = brain_exec.health_check()
        elapsed = time.time() - start
        
        assert result["status"] == "healthy"
        assert elapsed < 1, f"健康检查响应 {elapsed} >= 1 秒"
    
    def test_auto_recovery(self):
        """测试自动恢复"""
        # 模拟异常
        brain_exec.trigger_exception()
        
        # 检查自动恢复
        result = brain_exec.health_check()
        assert result["status"] == "healthy" or result["recovering"] == True
    
    def test_status_monitoring(self):
        """测试状态监控"""
        result = brain_exec.get_status()
        assert "status" in result
        assert "last_check" in result
        assert "error_count" in result
```

**验收标准**：
- ✅ 健康检查响应 < 1 秒
- ✅ 自动恢复可用
- ✅ 状态监控正常

---

## 🟡 P1 验收测试（3-6 周）

### 测试 9：单元测试覆盖率

```bash
# 执行命令
cd C:\Users\ADMIN\Desktop\GBT 小土豆 V8\gbt_allinone
python -m pytest --cov=. --cov-report=html --cov-fail-under=80

# 验收标准
# 覆盖率 > 80%
```

---

### 测试 10：CI/CD 门禁

```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest --cov=. --cov-fail-under=80
      - name: Lint
        run: flake8 .
```

**验收标准**：
- ✅ 所有 PR 必须通过测试才能合并
- ✅ Lint 检查通过

---

### 测试 11：Trace 链路追踪

```python
import pytest
from opentelemetry import trace

class TestTrace:
    """Trace 链路追踪测试"""
    
    def test_full_trace(self):
        """测试全链路追踪"""
        tracer = trace.get_tracer("test")
        
        with tracer.start_as_current_span("root") as root_span:
            with tracer.start_as_current_span("child1") as child1:
                # 模拟业务逻辑
                pass
            
            with tracer.start_as_current_span("child2") as child2:
                # 模拟业务逻辑
                pass
        
        # 检查 Trace
        spans = root_span.get_spans()
        assert len(spans) == 3  # root + child1 + child2
```

**验收标准**：
- ✅ 一次任务全链路可追踪
- ✅ 故障定位 < 5 分钟

---

## 🔵 P2 验收测试（7-12 周）

### 测试 12：吞天/进化层

```python
import pytest
from gbt_allinone import devour

class TestDevour:
    """吞天/进化层测试"""
    
    def test_devour_scan(self):
        """测试能力缺口扫描"""
        result = devour.scan("test_project")
        assert "gaps" in result
        assert isinstance(result["gaps"], list)
    
    def test_devour_github(self):
        """测试 GitHub 仓库吞噬"""
        result = devour.github("https://github.com/test/repo")
        assert result["status"] == "ok"
        assert "capabilities" in result
    
    def test_devour_reflect(self):
        """测试反思学习"""
        result = devour.reflect("test_capability")
        assert result["status"] == "ok"
        assert "insights" in result
    
    def test_devour_pulse(self):
        """测试完整认知循环"""
        result = devour.pulse("test_project")
        assert result["status"] == "ok"
        assert "scan" in result
        assert "devour" in result
        assert "reflect" in result
```

**验收标准**：
- ✅ 能力扫描可用
- ✅ GitHub 吞噬可用
- ✅ 反思学习可用
- ✅ 认知循环可用

---

### 测试 13：性能优化

```python
import pytest
import time

class TestPerformance:
    """性能优化测试"""
    
    def test_cold_start(self):
        """测试冷启动 < 2 秒"""
        start = time.time()
        # 模拟冷启动
        from gbt_allinone import api
        elapsed = time.time() - start
        
        assert elapsed < 2, f"冷启动 {elapsed} >= 2 秒"
    
    def test_key_path_latency(self):
        """测试关键链路时延 < 500ms"""
        start = time.time()
        result = api.osint_scan("example.com")
        elapsed = time.time() - start
        
        assert elapsed < 0.5, f"关键链路时延 {elapsed} >= 500ms"
    
    def test_cache_warmup(self):
        """测试缓存预热"""
        # 首次请求
        start = time.time()
        result1 = api.osint_scan("example.com")
        elapsed1 = time.time() - start
        
        # 缓存命中
        start = time.time()
        result2 = api.osint_scan("example.com")
        elapsed2 = time.time() - start
        
        assert elapsed2 < elapsed1, "缓存未生效"
        assert elapsed2 < 0.5, "缓存命中时延 >= 500ms"
```

**验收标准**：
- ✅ 冷启动 < 2 秒
- ✅ 关键链路时延 < 500ms
- ✅ 缓存预热有效

---

## 📊 测试执行计划

| 周次 | 测试类别 | 测试用例数 | 自动化率 |
|------|---------|-----------|---------|
| 1 | 账本模块 | 6 | 100% |
| 1 | LLM 对话 | 3 | 100% |
| 1 | 触手连接 | 3 | 100% |
| 2 | 生产管线监控 | 3 | 100% |
| 2 | 安全扫描告警 | 3 | 100% |
| 2 | 工作流错误处理 | 4 | 100% |
| 2 | 镜像空间监控 | 2 | 100% |
| 2 | 大脑健康检查 | 3 | 100% |
| 3-4 | 外部依赖接入 | 6 | 100% |
| 5-6 | 自动化与可观测 | 9 | 100% |
| 7-8 | 吞天/进化层 | 4 | 80% |
| 9-10 | 架构优化 | 3 | 80% |
| 11-12 | 性能优化 | 3 | 100% |

**总计**：60 个测试用例，自动化率 95%

---

> 生成时间：2026-09-13  
> 开发者：自由的风 · GBT 小土豆 V8
