# 🐾 汪星图鉴 · 犬类品种识别与科普系统

> **PawPedia** —— 一个前后端分离的犬类品种识别与科普系统。
> 上传一张狗狗照片，识别品种、置信度和 Top-3 候选，并顺手给你一张科普卡片。

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.165-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.5-42B883?logo=vuedotjs&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C?logo=pytorch&logoColor=white)

![首页](screenshots/home.png)

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [使用示例](#使用示例)
- [API 一览](#api-一览)
- [数据库设计](#数据库设计)
- [模型训练与知识蒸馏](#模型训练与知识蒸馏)
- [实验结果](#实验结果)
- [页面截图](#页面截图)
- [常见问题](#常见问题)
- [后续计划](#后续计划)
- [说明与致谢](#说明与致谢)

---

## 项目简介

**汪星图鉴（PawPedia）** 把「犬类品种识别」做成了一套完整的 Web 系统：

- **识别**：上传图片，返回品种中文名、置信度、Top-3 候选；
- **科普**：每个品种都有中英文名、简介、性格、体型、饲养难度、原产地、参考价格；
- **记录**：登录后自动保存识别历史，支持查看和删除；
- **管理**：管理员可以看数据概览、管理用户、查看识别记录、编辑科普内容。

模型识别 **8 个类别**：

| 类别 | 说明 |
|---|---|
| 比格（Beagle） | 正样本 |
| 中华田园犬（Chinese Rural Dog） | 正样本，类内差异大，是难点 |
| 泰迪（Poodle / Teddy） | 正样本 |
| 萨摩耶（Samoyed） | 正样本 |
| 边牧（Border Collie） | 正样本 |
| 金毛（Golden Retriever） | 正样本 |
| 柯基（Welsh Corgi） | 正样本 |
| 橘猫（Orange Tabby） | **负样本 / 干扰类**，检验模型会不会把橘色动物误判成狗 |

项目分为两部分：

1. **Web 系统**：`backend/` + `frontend/`，负责页面、用户、记录、科普和管理端；
2. **模型训练**：`training/`，负责爬取数据、训练 CNN、知识蒸馏，产出可部署的模型权重。

> 模型测试集准确率为 **57.50%（276/480）**，页面里的演示图是挑选过的正确样本，整体准确率请以测试集数字为准。

---

## 功能特性

### 游客

- 浏览首页、犬类图鉴、品种详情
- 上传图片直接识别（不保存历史）
- 按品种名搜索、按体型筛选（小型犬 / 中型犬 / 大型犬 / 其他）

### 普通用户

- 注册、登录
- 识别后自动保存：图片、品种、置信度、时间
- 查看、删除自己的识别历史

### 管理员

- 数据概览：用户数、识别数、科普数、今日识别、热门品种
- 用户管理：调整角色、启用 / 禁用账号
- 识别记录：查看所有用户记录、删除
- 科普内容：新增、编辑、删除犬种卡片

### 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Vue Router + Pinia + Axios |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.x（本地开发可切 SQLite） |
| 模型 | PyTorch + torchvision，加载已训练好的 8 类 DogCNN，只做推理 |
| 鉴权 | JWT + PBKDF2-SHA256 密码哈希 |
| 文档 | FastAPI 自动生成 Swagger / ReDoc |

---

## 系统架构

```
┌──────────────────────┐
│  Vue 3 + Vite 前端    │
│  页面 / 路由 / Pinia  │
└──────────┬───────────┘
           │  /api  (axios + JWT)
           ▼
┌──────────────────────┐
│  FastAPI 后端         │
│  ├─ 用户 / 鉴权       │
│  ├─ 图片识别          │
│  ├─ 科普 / 历史       │
│  └─ 管理端            │
└──────┬────────┬──────┘
       │        │
       ▼        ▼
┌──────────┐  ┌──────────────────────┐
│ MySQL    │  │ PyTorch DogCNN (8类)  │
│ SQLAlchemy│ │ backend/models/*.pth  │
└──────────┘  └──────────────────────┘
```

- 用户上传图片 → 后端保存到 `backend/uploads/` → 模型推理 → 返回识别结果；
- 登录用户的结果写入 `recognition_records` 表；
- 科普图片和品种信息由 `breeds` 表提供；
- 管理员通过 `/api/admin/*` 接口管理数据。

---

## 项目结构

```
pawpedia/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口、CORS、静态目录
│   │   ├── config.py            # 环境变量、数据库地址
│   │   ├── database.py          # SQLAlchemy 引擎与会话
│   │   ├── models.py            # User / Breed / RecognitionRecord
│   │   ├── schemas.py           # Pydantic 请求与响应
│   │   ├── security.py          # PBKDF2 + JWT
│   │   ├── deps.py              # 当前用户 / 管理员依赖
│   │   ├── seed.py              # 默认账号 + 8 个品种科普
│   │   ├── ml/predictor.py      # 模型加载与推理
│   │   └── routers/
│   │       ├── auth.py          # 注册 / 登录 / 当前用户
│   │       ├── breeds.py        # 公开科普接口
│   │       ├── recognition.py   # 图片识别
│   │       ├── history.py       # 用户历史
│   │       └── admin.py         # 管理端
│   ├── models/
│   │   └── dog_classification_model.pth
│   ├── static/breeds/           # 8 张品种图片
│   ├── uploads/                 # 用户上传图片
│   ├── scripts/init_mysql.sql
│   ├── requirements.txt
│   ├── .env                     # 本地开发配置（默认 SQLite）
│   ├── .env.example             # MySQL 示例
│   └── run.py
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # axios + 接口封装
│   │   ├── assets/styles.css    # 可爱萌宠主题
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
├── training/                    # 模型训练与蒸馏（数据集不随仓库提供）
│   ├── 1.download_data.py       # 百度图片爬虫（8 类 × 300 张）
│   ├── 2.split_data.py          # 8:2 划分
│   ├── 3.train_cnn.py           # 训练教师 DogCNN
│   ├── 4.classifier_ui.py       # Tkinter 调试界面（可选）
│   ├── 6.distillation_cnn.py    # 知识蒸馏（教师 → 学生）
│   ├── images/                  # 8 张演示图
│   ├── requirements.txt
│   └── user_info.txt
│
├── screenshots/                 # 页面截图 + 训练曲线
├── README.md
└── .gitignore
```

> `training/` 只包含代码和少量演示图，不包含 2400 张训练图片和训练集/测试集，避免仓库过大。
> 需要复现训练时，在 `training/` 目录运行爬虫即可重新采集。

---

## 快速开始

### 环境要求

- Python 3.10+（推荐 3.12）
- Node.js 18+（推荐 20/22）
- MySQL 8.x（可选；本地开发默认 SQLite）
- 内存 8GB+；CPU 也能跑，有 NVIDIA GPU 会自动使用 CUDA

### 1. 启动后端

```powershell
cd backend
python -m pip install -r requirements.txt
python run.py
```

启动后：

- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

首次启动会自动：

- 创建数据库表；
- 写入 2 个默认账号；
- 写入 8 个品种科普卡片。

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5173

### 3. 默认账号

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123456` |

> `training/4.classifier_ui.py` 是模型调试用的 Tkinter 界面，它自己的账号是 `admin / 123456`，与 Web 系统不同。

### 4. 切换到 MySQL

本地开发默认 SQLite，开箱即用。要按要求使用 MySQL：

```powershell
mysql -u root -p < backend\scripts\init_mysql.sql
```

先复制配置模板（仓库不会提交 `.env`）：

```powershell
Copy-Item backend\.env.example backend\.env
```

然后修改 `backend/.env`：

```env
DATABASE_URL=mysql+pymysql://pawpedia:pawpedia123@127.0.0.1:3306/pawpedia?charset=utf8mb4
SECRET_KEY=换成一串足够长的随机字符串
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_UPLOAD_MB=8
```

重启后端即可。SQLAlchemy 会自动建表并初始化数据。

---

## 使用示例

### 方式一：直接打开页面

1. 打开 http://127.0.0.1:5173；
2. 点「图片识别」，上传一张狗狗照片；
3. 选择「开始识别」；
4. 游客可以直接看结果；登录后会自动保存到「我的记录」；
5. 点「犬类图鉴」搜索、筛选，查看品种详情。

### 方式二：调用 API

```bash
# 1. 登录拿 token
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123456"}'

# 2. 上传图片识别（把 <TOKEN> 换成上一步返回的 access_token）
curl -X POST http://127.0.0.1:8000/api/recognition/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@dog.jpg"
```

返回示例：

```json
{
  "prediction": {
    "name_cn": "比格",
    "confidence": 0.9987,
    "top3": [
      { "name_cn": "比格", "confidence": 0.9987 },
      { "name_cn": "边牧", "confidence": 0.0008 },
      { "name_cn": "柯基", "confidence": 0.0003 }
    ]
  },
  "breed": {
    "name_cn": "比格",
    "name_en": "Beagle",
    "origin": "英国",
    "size_category": "中型犬"
  },
  "saved": true,
  "record_id": 1
}
```

> 不登录时 `saved` 为 `false`，不会写历史记录。

---

## API 一览

启动后端后访问 **http://127.0.0.1:8000/docs** 可直接在线调试。

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/auth/register` | 注册 | 公开 |
| POST | `/api/auth/login` | 登录 | 公开 |
| GET | `/api/auth/me` | 当前用户 | 用户 |
| GET | `/api/breeds` | 品种列表（search / size） | 公开 |
| GET | `/api/breeds/by-slug/{slug}` | 按 slug 查品种 | 公开 |
| GET | `/api/breeds/{id}` | 按 ID 查品种 | 公开 |
| GET | `/api/recognition/info` | 模型类别 / 准确率 / 设备 | 公开 |
| POST | `/api/recognition/predict` | 上传图片识别 | 公开（登录后保存） |
| GET | `/api/history` | 我的历史记录 | 用户 |
| DELETE | `/api/history/{id}` | 删除历史 | 用户 |
| GET | `/api/admin/overview` | 数据概览 | 管理员 |
| GET | `/api/admin/users` | 用户列表 | 管理员 |
| PATCH | `/api/admin/users/{id}` | 改角色 / 启用状态 | 管理员 |
| GET | `/api/admin/records` | 全部识别记录 | 管理员 |
| DELETE | `/api/admin/records/{id}` | 删除记录 | 管理员 |
| POST | `/api/admin/breeds` | 新增科普 | 管理员 |
| PUT | `/api/admin/breeds/{id}` | 编辑科普 | 管理员 |
| DELETE | `/api/admin/breeds/{id}` | 删除科普 | 管理员 |

---

## 数据库设计

| 表 | 作用 | 关键字段 |
|---|---|---|
| `users` | 用户 | username、password_hash、nickname、role、is_active |
| `breeds` | 犬种科普 | slug、name_cn、name_en、intro、personality、size_category、difficulty、origin、market_price、image_url、is_dog |
| `recognition_records` | 识别记录 | user_id、image_url、predicted_name、confidence、top3、created_at |

关系：

```
users 1 ─── n recognition_records
breeds 独立存储（识别结果按 name_cn 关联科普卡片）
```

---

## 模型训练与知识蒸馏

### 数据与任务

- 8 类 × 300 张 = **2400 张**
- 训练集 1920 张（每类 240），测试集 480 张（每类 60）
- 数据来源：百度图片 JSON 接口
- 爬虫做了 Cookie 预热、Content-Type 校验、PIL 校验、MD5 去重、限速
- 数据集不随仓库提供，运行 `training/1.download_data.py` 重新采集

### 训练代码

```powershell
cd training
python -m pip install -r requirements.txt
python 1.download_data.py
python 2.split_data.py
python 3.train_cnn.py
```

训练完成后：

- `training/models/dog_classification_model.pth`
- `training/results/training_history.png`
- `training/results/prediction_<类别>.png`

把模型复制到 Web 系统：

```powershell
Copy-Item training\models\dog_classification_model.pth backend\models\
```

### DogCNN 结构

```
输入 [3, 128, 128]
Conv(3→32)   + ReLU + MaxPool → [32, 64, 64]
Conv(32→64)  + ReLU + MaxPool → [64, 32, 32]
Conv(64→128) + ReLU + MaxPool → [128, 16, 16]
Conv(128→128)+ ReLU + MaxPool → [128, 8, 8]
Flatten → Dropout(0.5) → Linear(8192→256) → ReLU → Dropout(0.5) → Linear(256→8)
```

- 约 234 万参数；
- 输入 128×128，ImageNet 均值方差归一化；
- 训练集：随机旋转 ±20°、水平翻转、RandomResizedCrop(0.8~1.0)；
- 测试集只做 Resize + Normalize；
- 60 epoch，Adam lr=1e-3，每 20 轮学习率 ×0.5。

### 知识蒸馏

用教师模型的软标签指导学生模型：

```
Loss = α · T² · KL( softmax(student/T) ‖ softmax(teacher/T) )
       + (1 - α) · CrossEntropy(student, label)
```

参数：`T=4`，`α=0.7`。

```powershell
cd training
python 6.distillation_cnn.py
```

输出：

- `training/models/distilled_dog_model.pth`
- `training/results/distillation_history.png`
- `training/results/distillation_result.txt`

> 由于教师本身只有 57.5%，学生同结构蒸馏后为 56.67%，没有超过教师。
> 这属于“弱教师 + 同结构学生”的正常结果；想看到收益，建议换更强的教师（如 ResNet18）。

### ResNet18 对照实验

在同样 8 类数据上，冻结 ImageNet 预训练 ResNet18 主干、只训练线性分类头：

| 模型 | 测试准确率 |
|---|---|
| 4 层 CNN（当前部署） | **57.50%（276/480）** |
| ResNet18 预训练 + 线性头 | **90.62%（435/480）** |

ResNet18 目前只作为对照实验，未接入 Web 系统。

### 训练曲线

![训练曲线](screenshots/training/training_history.png)

![蒸馏曲线](screenshots/training/distillation_history.png)

---

## 实验结果

### 主模型

| 项目 | 结果 |
|---|---|
| 训练集 / 测试集 | 1920 / 480（每类 240 / 60） |
| 训练轮数 | 60 |
| 测试集准确率 | **57.50%（276/480）** |
| 最佳轮次 | 第 60 轮 |
| 训练耗时 | 约 24.1 分钟（CPU） |

### 各类别准确率

| 类别 | 正确/总数 | 准确率 |
|---|---|---|
| 萨摩耶 | 44 / 60 | 73% |
| 柯基 | 41 / 60 | 68% |
| 边牧 | 39 / 60 | 65% |
| 比格 | 36 / 60 | 60% |
| 中华田园犬 | 35 / 60 | 58% |
| 泰迪 | 30 / 60 | 50% |
| 金毛 | 27 / 60 | 45% |
| 橘猫 | 24 / 60 | 40% |

### 主要问题

1. **颜色捷径**：金毛、橘猫、柯基都是橙黄色系，模型容易互相混淆；
2. **中华田园犬是“吸附类”**：混血群体、类内差异极大，很多“拿不准”的样本会被判成它；
3. **标签噪声**：百度图片里混有海报、卡通图、拼图、其他犬种；
4. **模型容量有限**：128×128 的 4 层 CNN 很难区分 8 个细粒度品种。

> 页面里的演示图是挑选过的正确样本，置信度约 98.55%~100%；整体准确率仍以 57.50% 为准。
> Tkinter 调试界面默认用 `T=0.7` 做置信度显示锐化，只影响显示，不影响准确率；Web API 返回原始 softmax 置信度。

### 历史版本

| 配置 | 测试准确率 |
|---|---|
| 5 类 × 150 张（旧版） | 69.33%（104/150） |
| 8 类 × 300 张（当前） | 57.50%（276/480） |
| 8 类 + ResNet18（对照） | 90.62%（435/480） |

---

## 页面截图

| 首页 | 犬类图鉴 |
|---|---|
| ![](screenshots/home.png) | ![](screenshots/encyclopedia.png) |

| 图片识别 | 登录 |
|---|---|
| ![](screenshots/e2e_recognize.png) | ![](screenshots/login.png) |

| 管理端概览 | 管理端用户 |
|---|---|
| ![](screenshots/e2e_admin_dashboard.png) | ![](screenshots/e2e_admin_users.png) |

| 管理端科普 | 识别历史 |
|---|---|
| ![](screenshots/e2e_admin_breeds.png) | ![](screenshots/e2e_history.png) |

---

## 常见问题

### Q1：前端请求 404 / 跨域？

开发时 Vite 已配置代理：

- `/api` → `http://127.0.0.1:8000`
- `/static`、`/uploads` → `http://127.0.0.1:8000`

确认后端在 8000 端口运行即可。

### Q2：提示“未找到模型文件”？

确认 `backend/models/dog_classification_model.pth` 存在。如果还没训练，可以在 `training/` 里训练，或从原项目复制。

### Q3：MySQL 连接失败？

- 确认 MySQL 服务已启动；
- 确认执行了 `backend/scripts/init_mysql.sql`；
- 确认 `.env` 的账号密码和 SQL 一致；
- 如果报 `caching_sha2_password`，安装 `cryptography` 即可。

### Q4：为什么默认是 SQLite？

为了方便本地快速体验，`.env` 默认使用 SQLite；代码和表结构完全兼容 MySQL，按「快速开始 → 切换到 MySQL」修改 `.env` 即可。

### Q5：为什么准确率只有 57.5%？

8 类犬种本身难区分，数据里有标签噪声，而且 128×128 的 4 层 CNN 容量有限。ResNet18 对照实验可以到 90.62%，但当前系统按选题要求保留 CNN 主模型。

### Q6：为什么演示图置信度接近 100%，整体却只有 57.5%？

`images/` 和 `screenshots/` 里用的是挑选过的、模型能正确识别的样本。整体测试集有 480 张，包含很多难图和噪声图。

### Q7：为什么不能改类别文件夹名？

模型 checkpoint 里保存了 `class_names`，类别顺序由文件夹名的 Unicode 排序决定：

```
中华田园犬 < 柯基 < 橘猫 < 比格 < 泰迪 < 萨摩耶 < 边牧 < 金毛
```

改了文件夹名，训练和预测的索引就会错位。

### Q8：Windows 训练报多进程错误？

保持 `num_workers=0`。训练脚本已经固定。

### Q9：爬虫返回 `Forbid spider access`？

需要先访问图片搜索首页拿 `BAIDUID` Cookie，再请求 `acjson` 接口；脚本已内置预热。如果百度接口再次变化，按浏览器 Network 面板重新抓包。

### Q10：训练要多久？

- 教师模型：CPU 约 24 分钟
- 蒸馏学生：CPU 约 28 分钟
- 有 NVIDIA GPU 会快很多

---

## 后续计划

- [ ] 将 ResNet18（90.62%）接入 Web 识别接口
- [ ] 增加摄像头实时识别
- [ ] 数据清洗与主动学习，降低标签噪声
- [ ] 模型压缩 / 蒸馏到更小的学生网络
- [ ] Docker Compose 一键部署
- [ ] 增加识别结果的混淆矩阵与置信度校准展示

---

## 说明与致谢

- 数据集通过百度图片接口采集，仅用于学习与技术演示，请尊重原图版权；
- 默认账号和密码仅用于本地演示，部署到公网前请务必修改；
- 模型准确率有限，识别结果仅供科普参考，不能用于专业犬种鉴定；
- 前端视觉参考了可爱萌宠风格，使用了 Vue 3、FastAPI、PyTorch 等开源生态。

如果这个项目对你有帮助，欢迎点一个 ⭐ Star。