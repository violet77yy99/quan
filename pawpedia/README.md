# 🐾 汪星图鉴 · 犬类品种识别与科普系统

> **PawPedia** —— 一个前后端分离的犬类品种识别与科普系统。
> 上传一张狗狗照片，识别品种、置信度和 Top-3 候选，并顺手给你一张科普卡片。

![首页](screenshots/home.png)

---

## 一、功能清单

### 游客

- 浏览首页、犬类图鉴、品种详情
- 上传图片直接识别（不保存记录）
- 按品种名搜索、按体型筛选（小型犬 / 中型犬 / 大型犬 / 其他）

### 普通用户

- 注册、登录
- 识别后自动保存历史记录（图片、结果、置信度、时间）
- 查看、删除自己的历史记录

### 管理员

- 数据概览：用户数、识别数、科普数、今日识别
- 用户管理：调整角色、启用/禁用账号
- 识别记录：查看所有用户记录、删除
- 科普内容：新增、编辑、删除犬种卡片

---

## 二、技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Vue Router + Pinia + Axios |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.x（本地演示可切 SQLite） |
| 模型 | PyTorch + torchvision，加载已训练好的 8 类 DogCNN，只做推理 |
| 鉴权 | JWT + PBKDF2 密码哈希 |
| 文档 | FastAPI 自动生成 Swagger / ReDoc |

---

## 三、项目结构

```
pawpedia/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、CORS、静态目录
│   │   ├── config.py            # 环境变量、路径、数据库地址
│   │   ├── database.py          # SQLAlchemy 引擎与会话
│   │   ├── models.py            # User / Breed / RecognitionRecord
│   │   ├── schemas.py           # Pydantic 请求与响应
│   │   ├── security.py          # 密码哈希、JWT
│   │   ├── deps.py              # 当前用户 / 管理员依赖
│   │   ├── seed.py              # 默认账号 + 8 个品种科普
│   │   ├── ml/
│   │   │   └── predictor.py     # 模型加载与推理
│   │   └── routers/
│   │       ├── auth.py          # 注册 / 登录 / 当前用户
│   │       ├── breeds.py        # 公开的科普接口
│   │       ├── recognition.py   # 图片识别
│   │       ├── history.py       # 用户历史
│   │       └── admin.py         # 管理端接口
│   ├── models/
│   │   └── dog_classification_model.pth
│   ├── static/breeds/           # 8 张品种图片
│   ├── uploads/                 # 用户上传图片
│   ├── scripts/init_mysql.sql
│   ├── requirements.txt
│   ├── .env                     # 本地演示（SQLite）
│   ├── .env.example             # MySQL 示例
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── api/                 # axios + 接口封装
│   │   ├── assets/styles.css    # 可爱萌宠风格
│   │   ├── components/          # Header / Footer / BreedCard / Toast…
│   │   ├── layouts/             # 前台布局 + 管理端布局
│   │   ├── router/              # 路由与权限守卫
│   │   ├── stores/              # Pinia：登录态、Toast
│   │   ├── views/               # 首页 / 识别 / 图鉴 / 历史 / 登录…
│   │   │   └── admin/           # 概览 / 用户 / 记录 / 科普
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── screenshots/                 # 页面截图
└── README.md
```

---

## 四、快速启动

### 1. 启动后端

```powershell
cd d:\quan\pawpedia\backend
python -m pip install -r requirements.txt
python run.py
```

启动后：

- API：http://127.0.0.1:8000
- Swagger 文档：http://127.0.0.1:8000/docs
- ReDoc 文档：http://127.0.0.1:8000/redoc

> 当前 `backend/.env` 默认使用 SQLite，开箱即可运行。
> 要按要求切到 MySQL，看下面「五、MySQL 配置」。

### 2. 启动前端

```powershell
cd d:\quan\pawpedia\frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5173

### 3. 默认账号

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123456` |

---

## 五、MySQL 配置

> 本机环境里 MySQL 只有客户端、没有 `mysqld.exe`，所以本地演示默认用 SQLite。
> 代码和 SQLAlchemy 模型完全兼容 MySQL，按下面三步即可切换。

### 1. 启动 MySQL 并初始化

用管理员账号执行：

```powershell
mysql -u root -p < backend\scripts\init_mysql.sql
```

脚本会创建：

- 数据库 `pawpedia`（utf8mb4）
- 用户 `pawpedia` / `pawpedia123`（localhost 和 127.0.0.1 都授权）

### 2. 修改 `backend/.env`

```env
DATABASE_URL=mysql+pymysql://pawpedia:pawpedia123@127.0.0.1:3306/pawpedia?charset=utf8mb4
SECRET_KEY=换成一串足够长的随机字符串
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_UPLOAD_MB=8
```

### 3. 重启后端

SQLAlchemy 会自动建表，并自动写入默认账号和 8 个品种科普。

> 从 SQLite 切到 MySQL 后，旧的 SQLite 数据不会迁移；新库会重新初始化。

---

## 六、接口文档

启动后端后访问 **http://127.0.0.1:8000/docs**，可以直接在线调试。

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/auth/register` | 注册 | 公开 |
| POST | `/api/auth/login` | 登录 | 公开 |
| GET | `/api/auth/me` | 当前用户 | 用户 |
| GET | `/api/breeds` | 品种列表（search / size） | 公开 |
| GET | `/api/breeds/by-slug/{slug}` | 按 slug 查品种 | 公开 |
| GET | `/api/breeds/{id}` | 按 ID 查品种 | 公开 |
| GET | `/api/recognition/info` | 模型类别/准确率/设备 | 公开 |
| POST | `/api/recognition/predict` | 上传图片识别 | 公开（登录后保存） |
| GET | `/api/history` | 我的历史记录 | 用户 |
| DELETE | `/api/history/{id}` | 删除历史 | 用户 |
| GET | `/api/admin/overview` | 数据概览 | 管理员 |
| GET | `/api/admin/users` | 用户列表 | 管理员 |
| PATCH | `/api/admin/users/{id}` | 改角色/启用状态 | 管理员 |
| GET | `/api/admin/records` | 全部识别记录 | 管理员 |
| DELETE | `/api/admin/records/{id}` | 删除记录 | 管理员 |
| POST | `/api/admin/breeds` | 新增科普 | 管理员 |
| PUT | `/api/admin/breeds/{id}` | 编辑科普 | 管理员 |
| DELETE | `/api/admin/breeds/{id}` | 删除科普 | 管理员 |

---

## 七、数据库表

| 表 | 作用 | 关键字段 |
|---|---|---|
| `users` | 用户 | username、password_hash、nickname、role、is_active |
| `breeds` | 科普内容 | slug、name_cn、name_en、intro、personality、size_category、difficulty、origin、market_price、image_url、is_dog |
| `recognition_records` | 识别记录 | user_id、image_url、predicted_name、confidence、top3、created_at |

---

## 八、模型说明

- 模型文件：`backend/models/dog_classification_model.pth`
- 结构：4 层 CNN（DogCNN），输入 128×128，输出 8 类
- 类别：中华田园犬、柯基、橘猫、比格、泰迪、萨摩耶、边牧、金毛
- 测试集准确率：**57.50%**（276/480）
- 只做推理，不包含训练代码；训练代码在 `d:\quan\dog_recognition`
- 单张图片推理流程：Resize(128) → ToTensor → ImageNet Normalize → softmax → Top-3

> 橘猫是模型里的“非犬类”干扰项，图鉴里标记为「非犬类」。

---

## 九、页面截图

| 页面 | 截图 |
|---|---|
| 首页 | ![](screenshots/home.png) |
| 犬类图鉴 | ![](screenshots/encyclopedia.png) |
| 图片识别 | ![](screenshots/e2e_recognize.png) |
| 登录 | ![](screenshots/login.png) |
| 管理端概览 | ![](screenshots/e2e_admin_dashboard.png) |
| 管理端用户 | ![](screenshots/e2e_admin_users.png) |
| 管理端科普 | ![](screenshots/e2e_admin_breeds.png) |

---

## 十、常见问题

### Q1：前端请求 404 / 跨域？

开发时 Vite 已配置代理：

- `/api` → `http://127.0.0.1:8000`
- `/static`、`/uploads` → `http://127.0.0.1:8000`

确认后端在 8000 端口运行即可。

### Q2：提示“未找到模型文件”？

确认 `backend/models/dog_classification_model.pth` 存在。如果模型在旧项目里，可以复制过来：

```powershell
Copy-Item d:\quan\dog_recognition\models\dog_classification_model.pth d:\quan\pawpedia\backend\models\
```

### Q3：MySQL 连接失败？

- 确认 MySQL 服务已启动；
- 确认已执行 `scripts/init_mysql.sql`；
- 确认 `.env` 里的账号密码和 SQL 一致；
- 如果报 `caching_sha2_password`，已安装 `cryptography` 即可。

### Q4：为什么本地默认是 SQLite？

本机只有 MySQL 客户端，没有服务端 `mysqld.exe`。为了让你先跑起来，默认用 SQLite；
代码、表结构、SQLAlchemy 用法完全兼容 MySQL，切换只需改 `.env`。

### Q5：管理员账号怎么改？

在管理端「用户管理」里可以把普通用户提升为管理员；默认管理员是 `admin / admin123`。

---

## 十一、开发约定

- 前端页面使用 Vue 3 `<script setup>`，接口统一走 `src/api`。
- 后端所有接口统一前缀 `/api`，自动文档在 `/docs`。
- 上传图片限制 8MB，保存在 `backend/uploads/`，通过 `/uploads/...` 访问。
- 密码使用 PBKDF2-SHA256 哈希，JWT 有效期 7 天。
- 生产环境请修改 `SECRET_KEY`、MySQL 密码，并用 Nginx 反向代理前后端。