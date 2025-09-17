## 图书馆座位自动预约脚本（DLUFL 示例）

本项目提供一个基于 Playwright 的“配置驱动”自动预约脚本。通过 YAML 配置选择器与页面 URL，即可适配 `http://lib.dlufl.edu.cn`（或类似系统）。

### 1. 环境准备

- 安装依赖：
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

- 复制环境变量模板，并填写账号密码：
```bash
cp .env.example .env
```

- 复制配置模板，并按实际页面选择器修改：
```bash
cp config.example.yaml config.yaml
```

> 提示：用浏览器开发者工具检查输入框、按钮、座位元素的选择器，并写入 `config.yaml`。

### 2. 用法

首次运行建议“有头模式”（非 headless），方便定位/更新选择器。

```bash
python -m auto_seat.cli \
  --config config.yaml \
  --seat 305 \
  --date tomorrow \
  --start 08:00 \
  --end 22:00 \
  --open-time 06:59:58 \
  --headless
```

- `--seat`: 座位号或座位 ID。
- `--date`: `YYYY-MM-DD` / `today` / `tomorrow`。
- `--start` / `--end`: 开始/结束时间（HH:MM）。
- `--open-time`: 在某一时刻自动“卡点”提交（可选）。
- `--headless`: 使用无头浏览器（可选，不加则默认有头）。
- `--config`: 配置文件路径，默认 `config.yaml`。

凭据获取：默认从环境变量 `AUTO_SEAT_USERNAME`、`AUTO_SEAT_PASSWORD` 读取；也可通过 `--username`、`--password` 明确传入。

持久化登录：首次登录后会将会话保存在 `~/.auto_seat`（或 `.env` 的 `AUTO_SEAT_STORAGE` 指定目录）中。

### 3. 配置说明（摘录）

```yaml
base_url: "http://lib.dlufl.edu.cn"
login:
  url: "http://lib.dlufl.edu.cn/portal/login"
  username_selector: "input[name='username']"
  password_selector: "input[name='password']"
  submit_selector: "button[type='submit']"
reservation:
  url: "http://lib.dlufl.edu.cn/seat/reserve"
  # 二选一：
  # seat_selector_template: "button[data-seat='{seat}']"
  # seat_page_template: "http://lib.dlufl.edu.cn/seat/{seat}/reserve"
```

### 4. 定时运行（crontab）

例如：每天 06:59:50 启动脚本，卡点 `--open-time 07:00:00` 提交。

```bash
crontab -e
# 分 时 日 月 周  命令
50 6 * * * cd /path/to/workspace && /usr/bin/python -m auto_seat.cli --config /path/to/config.yaml --seat 305 --date tomorrow --start 08:00 --end 22:00 --open-time 07:00:00 --headless >> /path/to/auto_seat.log 2>&1
```

### 5. 常见问题

- 按钮/输入框定位不到：更新 `config.yaml` 中的选择器；或先去掉 `--headless` 观察页面。
- 登录后仍跳回登录页：清理 `~/.auto_seat` 目录后重试；或检查是否有统一认证/验证码流程，必要时先手动登录一次。
- 预约失败但无报错：在有头模式观察弹窗提示，补齐 `result_success_selector` / `result_failure_selector`。