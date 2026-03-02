# MT5 跟单桌面软件（可直接运行）

这是一个可以直接运行的 Python 桌面项目，包含：

- 跟单引擎（正向 / 反向）
- 指定手数 / 比例手数
- 指定 Magic 跟单
- 浮盈 / 浮亏触发过滤
- 风控限制（最大持仓笔数、最大总手数）
- SQLite 映射与日志持久化
- 桌面 GUI（规则配置、启动/停止、模拟信号验证）

> 默认使用 `FakeMT5Client` 进行可运行验证。接入实盘时可切换到 `MT5Client`。

## 1. 环境准备

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. 运行

```bash
mt5-copier
# 或
python -m copier.main
```

运行后可在界面中：

1. 设置跟单规则（反向、固定手、比例手、Magic 白名单）
2. 点击“启动”
3. 点击“模拟一笔信号”验证跟单链路
4. 查看 `copier.db` 中订单映射和日志

## 3. 测试

```bash
pytest -q
```

## 4. 切换到真实 MT5

`copier/adapters/mt5_client.py` 提供 `MT5Client`：

- 安装：`pip install MetaTrader5`
- 启动 MT5 终端并允许算法交易
- 用真实账号信息构造 `MT5Client` 替换 `FakeMT5Client`

## 5. 项目结构

```text
copier/
  adapters/        # MT5 适配层（Fake + Real）
  core/            # 规则、引擎、服务编排
  storage/         # SQLite 持久化
  ui/              # 桌面 GUI
  main.py          # 应用入口
tests/
```
