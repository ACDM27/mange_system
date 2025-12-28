# Student Information Service Platform - Backend API

基于 FastAPI 的学生综合信息服务平台后端 API，提供学生成果管理、AI 分析和导师管理功能。

## 功能特性

### 核心模块
- **认证系统**: JWT 基于令牌的身份验证
- **角色管理**: 学生端和管理端分离
- **成果管理**: 学生提交成果，管理员审核
- **OCR 识别**: 智能识别证书信息
- **AI 对话**: 带上下文管理的 AI 导师对话
- **学生画像**: AI 生成的学生综合画像

### API 模块
- `/api/v1/auth/*` - 认证模块
- `/api/v1/common/*` - 公共接口（教师列表、文件上传）
- `/api/v1/student/*` - 学生端接口
- `/api/v1/admin/*` - 管理端接口

## 技术栈

- **框架**: FastAPI 0.109.0
- **数据库**: MySQL + SQLAlchemy ORM
- **认证**: JWT (python-jose)
- **密码加密**: Bcrypt (passlib)
- **异步支持**: Uvicorn + aiofiles

## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

关键配置项：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `LLM_API_KEY`: AI 大模型 API 密钥
- `OCR_API_URL`: OCR 服务地址

### 4. 初始化数据库

```bash
python init_db.py
```

这将创建所有数据表并插入测试数据。

### 5. 启动服务

```bash
# 开发模式（热重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将运行在 `http://localhost:8000`

### 6. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试账号

运行 `init_db.py` 后，可使用以下测试账号：

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 管理端登录 |
| 学生 | student001 | password123 | 张三 - 计算机专业 |
| 学生 | student002 | password123 | 李四 - 软件工程 |

## 数据库架构

### 核心表
- `sys_users` - 系统用户表
- `sys_teachers` - 教师基础数据表
- `sys_students` - 学生档案表
- `biz_achievements` - 成果表
- `ai_chat_sessions` - AI 会话表
- `ai_chat_messages` - AI 消息记录表

详细 ER 设计见设计文档。

## API 接口示例

### 登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"student001","password":"password123"}'
```

### 提交成果（需要 Token）
```bash
curl -X POST "http://localhost:8000/api/v1/student/achievements" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "全国大学生数学建模竞赛一等奖",
    "teacher_id": 1,
    "type": "competition",
    "content_json": {},
    "evidence_url": "/uploads/cert.jpg"
  }'
```

### 获取我的成果
```bash
curl -X GET "http://localhost:8000/api/v1/student/achievements?status=approved" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py              # 配置管理
├── database.py            # 数据库连接
├── models.py              # SQLAlchemy 模型
├── schemas.py             # Pydantic 模式
├── auth.py                # 认证工具
├── dependencies.py        # FastAPI 依赖
├── utils.py               # 工具函数
├── init_db.py             # 数据库初始化脚本
├── routers/               # API 路由
│   ├── __init__.py
│   ├── auth.py           # 认证接口
│   ├── common.py         # 公共接口
│   ├── student.py        # 学生端接口
│   └── admin.py          # 管理端接口
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
└── README.md             # 本文件
```

## AI 集成说明

### OCR 识别
目前 `/api/v1/student/ocr/recognize` 接口返回模拟数据。生产环境需要：
1. 配置 `OCR_API_URL` 和相关 API 密钥
2. 修改 `routers/student.py` 中的 OCR 调用逻辑
3. 适配具体 OCR 服务的请求/响应格式

### AI 对话
目前 `/api/v1/student/ai/chat` 接口返回模拟回复。生产环境需要:
1. 配置 `LLM_API_URL` 和 `LLM_API_KEY`
2. 修改 `routers/student.py` 中的 LLM 调用逻辑
3. 实现完整的 RAG（检索增强生成）逻辑

推荐的 LLM 服务：
- OpenAI GPT-4
- Google Gemini
- Azure OpenAI
- 国内大模型（通义千问、文心一言等）

## 生产部署建议

1. **安全性**
   - 修改 `SECRET_KEY` 为强随机字符串
   - 使用 HTTPS
   - 配置防火墙和 API 限流

2. **数据库**
   - 使用连接池
   - 定期备份
   - 优化索引

3. **文件存储**
   - 使用对象存储（OSS/S3）替代本地文件
   - 修改 `routers/common.py` 的上传逻辑

4. **日志监控**
   - 添加日志系统（Loguru）
   - 配置 APM 监控
   - 错误追踪（Sentry）

5. **性能优化**
   - 启用 Redis 缓存
   - 异步任务队列（Celery）
   - 数据库读写分离

## 开发指南

### 添加新接口
1. 在对应的 router 文件中添加端点
2. 定义 Pydantic 模型在 `schemas.py`
3. 必要时更新数据库模型在 `models.py`
4. 使用 `success_response()` 和 `error_response()` 统一响应格式

### 权限控制
- 使用 `Depends(require_student)` 限制学生端
- 使用 `Depends(require_admin)` 限制管理端
- 使用 `Depends(get_current_user)` 获取当前用户

## 常见问题

**Q: 数据库连接失败？**  
A: 检查 `.env` 中的 `DATABASE_URL`，确保 MySQL 服务运行且数据库已创建。

**Q: Token 验证失败？**  
A: 确保请求头格式为 `Authorization: Bearer <token>`，Token 未过期。

**Q: 文件上传失败？**  
A: 检查 `uploads` 目录是否有写权限，文件大小是否超过限制。

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队。
