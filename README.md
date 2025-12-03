# OKX 持仓跟踪网页

一个基于 FastAPI 的轻量网页，自动拉取 OKX 交易所的持仓数据，持续导出最新盈亏到 Excel，并提供交易日志记录入口。

## 功能
- 后台定时轮询 OKX 持仓（默认 15 秒），缓存最新数据。
- 前端表格实时展示持仓、盈亏、标记价格等信息。
- 一键导出当前快照到 `positions.xlsx`。
- 通过 API 写入交易逻辑日志，便于复盘。

## 环境变量
| 变量 | 说明 |
| --- | --- |
| `OKX_API_KEY` | OKX API Key（必填） |
| `OKX_SECRET_KEY` | OKX Secret Key（必填） |
| `OKX_PASSPHRASE` | OKX Passphrase（必填） |
| `OKX_BASE_URL` | OKX API Base URL，默认 `https://www.okx.com` |
| `OKX_INST_TYPE` | 合约类型，默认 `SWAP` |
| `POLL_INTERVAL` | 轮询间隔（秒），默认 `15` |
| `DATA_DIR` | 数据根目录，默认 `data` |
| `EXCEL_PATH` | Excel 输出路径，默认 `data/positions.xlsx` |
| `TRADE_LOG_PATH` | 交易日志路径，默认 `data/logs/trade_journal.log` |

## 安装与运行
1. 创建虚拟环境并安装依赖：
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 设置环境变量（可写入 `.env`）：
   ```bash
   export OKX_API_KEY=your_key
   export OKX_SECRET_KEY=your_secret
   export OKX_PASSPHRASE=your_passphrase
   ```
3. 启动服务：
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. 浏览器访问 `http://localhost:8000/` 查看持仓与导出功能。

## API 简要
- `GET /positions`：返回缓存的最新持仓。
- `GET /refresh`：立即拉取 OKX，返回并刷新缓存。
- `GET /export`：下载最新 Excel。
- `POST /logs`：记录交易日志，示例：
  ```json
  {
    "message": "早盘突破做多 BTC",
    "context": "依据 1h 趋势线"
  }
  ```

## 备注
- Excel 使用 `openpyxl` 写入，目录会自动创建。
- 日志文件在 `data/logs/trade_journal.log` 中，可用于日常交易逻辑记录与复盘。
