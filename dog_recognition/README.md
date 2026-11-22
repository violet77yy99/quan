# 犬类品种分类系统 · 项目开发说明（核心版）

> 本项目参考「水果图像分类系统」的工程流水线，改为 **8 类犬/猫图像分类**：
>
> | 类别 | 说明 |
> |---|---|
> | 比格（Beagle） | 正样本 |
> | 中华田园犬 | 正样本（类内差异大，是难点） |
> | 泰迪（Poodle） | 正样本 |
> | 萨摩耶（Samoyed） | 正样本 |
> | 边牧（Border Collie） | 正样本 |
> | 金毛（Golden Retriever） | 正样本 |
> | 柯基（Corgi） | 正样本 |
> | 橘猫 | **负样本/干扰类**，检验模型是否会把橘色动物误判为犬 |
>
> 核心版包含 4 个基础脚本：**数据采集 → 数据划分 → CNN 训练 → 图形界面预测**；
> 另附可选的 `6.distillation_cnn.py`，演示**教师 → 学生知识蒸馏**。
> 摄像头版、集成预测属于后续扩展（见第 9 节）。

---

## 1. 项目目标

完成一条从数据到界面的最小可运行闭环：

```
百度图片爬虫  →  8:2 划分  →  4 层 CNN 训练  →  登录 + 选图 + 预测界面
    ①              ②              ③                    ④
```

- 输入：任意 RGB 图片，统一缩放到 128×128
- 输出：类别名称 + 置信度（Softmax 概率），界面额外显示 Top-3
- 训练设备：自动选择 CUDA，无 GPU 时回退 CPU（本机为 CPU 版）

---

## 2. 目录结构

```
dog_recognition/
├── 1.download_data.py        # ① 百度图片爬虫（8 类，每类 300 张）
├── 2.split_data.py           # ② 训练/测试集 8:2 划分（固定种子 42）
├── 3.train_cnn.py            # ③ DogCNN 训练、评估、曲线、单张预测演示
├── 4.classifier_ui.py        # ④ 登录 + 选图 + 预测（Tkinter）
├── 6.distillation_cnn.py     # ⑤ 知识蒸馏（教师 → 学生）
├── user_info.txt             # 登录账号
├── requirements.txt          # 依赖版本
├── README.md                 # 开发说明（工程视角）
├── 技术文档.md               # 目录与技术说明（每个目录做什么）
│
├── dog_images/               # 【原始数据】按类别分文件夹
│   └── {比格,中华田园犬,泰迪,萨摩耶,边牧,金毛,柯基,橘猫}/
├── dog_images_split/         # 【划分后数据】运行 ② 后生成
│   ├── train/{8 个类别}/     # 每类 240 张
│   └── test/{8 个类别}/      # 每类 60 张
├── images/                   # 界面演示图片（每类 1 张，已挑选正确样本）
├── models/
│   ├── dog_classification_model.pth   # 教师模型，④ 默认读取
│   └── distilled_dog_model.pth        # 学生模型（蒸馏输出）
├── logs/
│   ├── download.log          # 最终爬虫日志
│   ├── train.log             # 教师训练日志
│   └── distillation.log      # 蒸馏训练日志
├── results/
│   ├── training_history.png  # ③ 生成的训练曲线
│   ├── prediction_<类别>.png  # ③ 生成的单张预测可视化
│   ├── data_preview.png      # 各类样本抽样预览（人工质检）
│   ├── misclassified.png     # 测试集全部错分样本汇总
│   ├── distillation_history.png  # 蒸馏训练曲线
│   ├── distillation_result.txt   # 教师/学生结果摘要
│   └── screenshots/
│       ├── login_window.png  # 登录窗口截图
│       └── demo_window.png   # 演示模式截图
└── tools/
    └── capture_window.ps1    # 可选的窗口截图脚本
```

**关键约定：训练输出与界面读取使用同一个固定路径**
`3.train_cnn.py` 输出 `models/dog_classification_model.pth`，`4.classifier_ui.py` 默认读取它，训练完直接运行界面即可，不需要复制或改名。重新训练会覆盖旧模型，需要保留请先备份。

---

## 3. 环境准备

本项目实际验证环境：

| 组件 | 版本 |
|---|---|
| Python | 3.12.10 |
| torch | 2.15.0+cpu |
| torchvision | 0.29.2+cpu |
| OpenCV | 5.1.0（核心 4 脚本未使用，供后续摄像头扩展） |
| Pillow | 13.0.0 |
| matplotlib | 3.11.2 |
| tqdm | 4.70.1 |
| requests | 2.34.2 |
| 设备 | CPU（有 NVIDIA GPU 时自动使用 CUDA） |

安装命令：

```powershell
# CPU 版 PyTorch
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# 其余依赖
python -m pip install opencv-python pillow numpy matplotlib requests tqdm
```

> 有 NVIDIA 显卡时，到 https://pytorch.org 选择对应 CUDA 版本的安装命令；代码中的
> `torch.device('cuda' if torch.cuda.is_available() else 'cpu')` 会自动切换，无需改代码。

环境检查：

```python
import torch, torchvision, cv2, PIL
print("torch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("CUDA 可用:", torch.cuda.is_available())
print("OpenCV:", cv2.__version__)
```

**运行约定**

1. 所有脚本都必须在 `dog_recognition/` 目录下运行（全部使用相对路径）。
2. Windows 下 `num_workers` 必须为 0，代码中已固定。
3. matplotlib 使用 `Agg` 后端，只保存图片不弹窗，服务器/无 GUI 环境也不会报错。
4. 中文路径可以正常运行（PIL 按二进制流读图）。

---

## 4. 完整操作步骤

### 步骤 1：采集图片

```powershell
python 1.download_data.py
```

脚本行为：

1. 依次爬取「比格、中华田园犬、泰迪、萨摩耶、橘猫、边牧、金毛、柯基」，每类目标 300 张（`TARGET_PER_CLASS` 可改）；
2. 先访问图片搜索首页获取 `BAIDUID` Cookie，再请求 `acjson` JSON 接口；
3. 图片优先取 `thumburl`（百度 CDN 缩略图），保存到 `./dog_images/<类别>/`；
4. 下载后用 PIL 校验格式与尺寸，过小（短边 <100px）、损坏、小于 5KB 的图片直接删除；
5. 按文件 MD5 去重，重复运行不会重复落盘；
6. 每张间隔 0.2s、每页间隔 1.2s，降低反爬风险。

预期输出：

```
========== 开始爬取「比格」（关键词：比格犬）==========
  已新增 20 张（目录共 20 张）
  ...
「比格」本次新增 300 张，目录现有 300 张。
...
============================================================
爬取完成，统计：
  比格       共  300 张（本次新增 300 张）
  ...
```

**检查点**：`dog_images/` 下出现 8 个类别文件夹，每类 300 张。

> ⚠️ 百度接口会变。2026-11 实测：**不带 Cookie 直接请求会返回 `{"antiFlag":1,"message":"Forbid spider access"}`**，脚本已内置 Cookie 预热。如果将来彻底失效，请按第 8 节的方法重新抓包。

### 步骤 2：划分训练/测试集

```powershell
python 2.split_data.py
```

- 逐类别用固定种子 42 打乱；
- 前 80% 复制到 `train/`，后 20% 复制到 `test/`；
- 每次运行先清空 `dog_images_split/`，避免旧文件残留；
- 用 `os.listdir + 后缀集合` 收集图片，规避 Windows 上按后缀 `glob` 导致的重复计数。

预期输出：

```
🐶「比格」：总 300 张 → 训练集 240 张 | 测试集 60 张
...
整体统计：训练集 1920 张 | 测试集 480 张
```

### 步骤 3：训练模型

```powershell
python 3.train_cnn.py
```

流程：扫描并校验图片 → 构建 DataLoader → 训练 60 epoch → 测试集评估 → 保存最优 checkpoint → 画曲线 → 混淆矩阵 → 单张预测演示。

关键配置：

| 项 | 值 |
|---|---|
| 输入尺寸 | 128×128 |
| Batch size | 32 |
| Epoch | 60（保存测试准确率最高的权重，本机最优在第 60 轮） |
| 优化器 | Adam, lr=1e-3；每 20 epoch 学习率 ×0.5 |
| 损失函数 | CrossEntropyLoss |
| 数据增强 | 随机旋转 ±20°、水平翻转、RandomResizedCrop(0.8~1.0) |
| 归一化 | ImageNet 均值/方差 |

预期输出：

```
使用计算设备：cpu
类别顺序（索引 → 名称）：
  0 → 中华田园犬
  1 → 柯基
  2 → 橘猫
  3 → 比格
  4 → 泰迪
  5 → 萨摩耶
  6 → 边牧
  7 → 金毛
...
Epoch 60 总结：
  训练损失: ... | 训练准确率: ...
  测试损失: ... | 测试准确率: ...
最后一轮测试准确率：...
保存的最优模型测试准确率：... (276/480)，Epoch 60
训练总耗时：... 分钟

混淆矩阵（行 = 真实类别，列 = 预测类别）：
真实\预测      中华田园犬   柯基   橘猫   比格   泰迪   萨摩耶   边牧   金毛
...
各类准确率：
  ...
模型已保存为：...\models\dog_classification_model.pth
训练曲线已保存：...\results\training_history.png
```

**检查点**：生成 `models/dog_classification_model.pth`、`results/training_history.png`、`results/prediction_<类别>.png`。

### 步骤 4：运行图形界面

正常模式（需要登录）：

```powershell
python 4.classifier_ui.py
```

1. 登录窗口输入 `admin` / `123456`（或 `user` / `123456`）；
2. 主界面点击「选择犬类图片」，文件对话框默认打开 `images/` 目录；
3. 点击「开始预测」，显示预测类别、置信度与 Top-3 概率。

课堂演示模式（跳过登录，自动载入 `images/比格.jpg` 并预测）：

```powershell
python 4.classifier_ui.py --demo
```

演示模式会直接显示比格样例的预测结果（置信度 100%），适合上课或答辩时快速展示。
注意：`images/` 下是按类别挑选的、模型能正确识别的 8 张样例；整体测试准确率仍以 57.50% 为准，不代表任意图片都有同样置信度。

界面默认对 logits 做 `T=0.7` 的温度缩放，让显示置信度更直观（准确率不变）。如需关闭：

```powershell
python 4.classifier_ui.py --temperature 1.0
```

或自定义锐化程度：

```powershell
python 4.classifier_ui.py --temperature 0.5
```

模型缺失时界面仍可打开，但预测按钮不可用，状态栏会提示先训练。

### 步骤 5（可选）：知识蒸馏

前置条件：`models/dog_classification_model.pth`（教师）已存在。

```powershell
python 6.distillation_cnn.py
```

输出：

- `models/distilled_dog_model.pth`：学生模型；
- `results/distillation_history.png`：蒸馏曲线；
- `results/distillation_result.txt`：教师/学生结果对比。

用学生模型做预测：

```powershell
python 4.classifier_ui.py --model models/distilled_dog_model.pth
```

---

## 5. 各模块实现详解

### 5.1 数据采集：`1.download_data.py`

#### 5.1.1 接口与反爬

请求地址：

```
https://image.baidu.com/search/acjson
    ?tn=resultjson_com
    &word=比格犬
    &pn=0            # 偏移量，不是页码，按 30 递增
    &rn=30           # 每页 30 条
    &ala=0
    &nojc=0
    &newReq=1
```

实测要点：

- **必须先访问搜索首页拿 `BAIDUID` Cookie**，否则直接返回 `antiFlag`；
- `ala=0`、`nojc=0`、`newReq=1` 三个参数缺一不可；
- 响应结构为 `{"data": {"images": [...]}}`，图片在 `data["images"]`；
- 每条记录优先取 `thumburl`（约 500px 的 CDN 缩略图，稳定），其次 `objurl`（原图，可能有防盗链）。

#### 5.1.2 下载校验与去重

```python
if "image" not in resp.headers.get("Content-Type", "").lower():
    return False                      # 链接失效时会返回 HTML 错误页

if os.path.getsize(tmp_path) < MIN_FILE_SIZE:
    return False                      # 小于 5KB 的占位图

digest = self._file_md5(tmp_path)
if digest in self.seen_hashes:
    return False                      # 内容重复（跨页/跨关键词/重复运行）

Image.open(fh).verify()               # 能否正常解码
if min(width, height) < MIN_SIDE:
    return False                      # 短边小于 100px
```

先写 `.part` 临时文件，全部校验通过后再 `os.replace` 成正式文件名，避免坏图落盘。

#### 5.1.3 数据质量提醒

百度搜索结果不可避免会混入：插画、表情包、其他犬种、同一张图的不同尺寸、标题党图片。脚本只能做技术校验（格式/尺寸/重复），**语义清洗仍需人工抽检**。建议训练前：

1. 随机打开每类 10~20 张，删除明显无关图片；
2. 尤其检查「中华田园犬」——该词覆盖的犬只外观差异极大，标签噪声最重；
3. 删除纯文字图、拼图、带大面积水印的图。

### 5.2 数据划分：`2.split_data.py`

```python
random.seed(42)
random.shuffle(images)
split_idx = int(len(images) * 0.8)
train = images[:split_idx]
test = images[split_idx:]
```

- **逐类别划分**，保证每类都有 8:2 的训练/测试样本；
- **固定种子**，保证每次划分一致、实验可复现；
- 用 `shutil.copy2` 复制而不是移动，原图保留。

Windows 坑：早期写法按多个后缀分别 `glob` 再累加，`glob` 底层 `fnmatch` 会先 `normcase` 转小写，导致 `*.jpg` 与 `*.JPG` 匹配同一批文件（例如 300 张被统计成 600 张）。本项目改为 **`os.listdir` + 后缀转小写 + 集合判断**。

### 5.3 模型训练：`3.train_cnn.py`

#### 5.3.1 数据容错

爬虫图片可能损坏、是灰度图或 RGBA 图，训练脚本做了两层防护：

1. 扫描阶段用 `Image.open(f).verify()` 校验，损坏/过小图片直接跳过；
2. `DogDataset.__getitem__` 中 `convert('RGB')` 统一三通道，读取失败时返回黑图兜底，避免训练中断。

#### 5.3.2 网络结构 `DogCNN`

```
输入 [3,128,128]
Conv(3→32)+ReLU+MaxPool    → [32,64,64]
Conv(32→64)+ReLU+MaxPool   → [64,32,32]
Conv(64→128)+ReLU+MaxPool  → [128,16,16]
Conv(128→128)+ReLU+MaxPool → [128,8,8]
Flatten → Dropout(0.5) → Linear(8192→256) → ReLU → Dropout(0.5) → Linear(256→8)
```

设计要点：

- `padding=1` + `kernel=3`：卷积不改变特征图尺寸，只有池化减半；
- 4 次池化：128 → 64 → 32 → 16 → 8；
- 通道 32→64→128→128：低层学边缘纹理，高层学语义；
- `Dropout(0.5)` 抑制小数据集过拟合；
- `128*8*8=8192` 是硬编码，改输入尺寸时必须同步改（例如 224 对应 `128*14*14`）。

#### 5.3.3 训练循环三件套

```python
optimizer.zero_grad()   # 1. 清空上批梯度
loss.backward()         # 2. 反向传播
optimizer.step()        # 3. 更新参数
```

- `model.train()` / `model.eval()` 必须切换，影响 Dropout 行为；
- 验证阶段 `torch.no_grad()`，不构建计算图；
- 损失按 `loss.item() * batch_size` 累加再除以样本总数，得到真实平均损失；
- 每个 epoch 结束后 `scheduler.step()`，学习率按 `StepLR(step_size=20, gamma=0.5)` 衰减；
- 训练过程中记录测试准确率最高的权重，训练结束后回滚保存该权重，而不是直接保存最后一轮。

#### 5.3.4 模型保存

```python
torch.save({
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "class_names": class_names,      # ★ 索引 → 类别名，预测时必须一致
    "final_accuracy": final_acc,     # 保存的最优模型准确率
    "best_test_acc": best_acc,
    "best_epoch": best_epoch,
    "last_test_acc": last_acc,       # 最后一轮准确率，用于对比过拟合
    "epochs": EPOCHS,
    "input_size": IMG_SIZE,
    "training_time_sec": elapsed,
    "history": history,
}, MODEL_PATH)
```

`class_names` 是最关键的一项：模型只输出 0~7 的索引，没有类别名就无法解释结果。类别顺序由文件夹名的 **Unicode 排序**决定：

```
中华田园犬 < 柯基 < 橘猫 < 比格 < 泰迪 < 萨摩耶 < 边牧 < 金毛
```

因此训练集和测试集必须使用完全相同的文件夹名。

### 5.4 图形界面：`4.classifier_ui.py`

#### 5.4.1 结构

```
启动 → 登录窗口(Tk #1) → 登录成功 destroy → 主界面(Tk #2)
```

登录账号支持 `用户名:密码`、`用户名 / 密码`、`用户名 密码` 三种写法，用户名忽略大小写，密码区分大小写。

#### 5.4.2 单张推理

```python
transform = Resize((128,128)) → ToTensor() → Normalize(...)
image = Image.open(path).convert("RGB")
tensor = transform(image).unsqueeze(0)     # [1, 3, 128, 128]

with torch.no_grad():
    outputs = model(tensor)                # logits
    # T=0.7 只用于显示层锐化；设为 1.0 即普通 softmax
    probs = torch.softmax(outputs / CONFIDENCE_TEMPERATURE, dim=1)
    top_probs, top_indices = torch.topk(probs, 3)
```

`unsqueeze(0)` 是单张推理的关键：模型永远按 batch 处理，单张图也要补成 `[1,C,H,W]`。

> 温度缩放不改变 argmax，因此**预测类别和准确率都不变**，只是让显示置信度更高；状态栏会标注“仅显示”。

#### 5.4.3 两个 Tkinter 经典坑

```python
self.image_frame.pack_propagate(False)   # 固定显示区域，防止大图挤出布局
self.image_label.photo = photo           # 必须持有引用，否则 PhotoImage 被回收
```

`PhotoImage` 不被 Tkinter 引用计数管理，局部变量回收后图片会变成空白。

### 5.5 知识蒸馏：`6.distillation_cnn.py`

#### 5.5.1 它解决什么问题

普通训练只使用真实标签（one-hot 硬标签），模型只知道“这张图是比格”，不知道“它有多像柯基”。

知识蒸馏让一个已经训练好的**教师模型**输出软标签（每个类别的概率分布），学生模型同时学习：

- 教师的软标签：包含类别之间的相似性（例如“金毛 0.55 / 橘猫 0.30 / 田园犬 0.15”）；
- 真实硬标签：保证答案不跑偏。

#### 5.5.2 损失函数

```
Loss = α · T² · KL( softmax(student/T) ‖ softmax(teacher/T) )
       + (1 - α) · CrossEntropy(student, label)
```

| 参数 | 含义 | 本项目取值 |
|---|---|---|
| `T` | 温度，越大分布越平滑，暗知识越明显 | 4.0 |
| `α` | 软损失权重，标准范围 [0,1] | 0.7 |
| `T²` | 抵消温度对梯度的缩放 | 自动乘上 |

> **与参考文档的差异**：参考文档 5.5 的实现写成 `alpha * soft_loss + 1.0 * hard_loss`，并取 `alpha=2.0`，这不是标准写法。
> 本项目按标准公式实现为 `alpha * soft_loss + (1 - alpha) * hard_loss`，`alpha=0.7`、`T=4`，可直接用于教学对比。

#### 5.5.3 核心代码

```python
class DistillationLoss(nn.Module):
    def __init__(self, temperature=4.0, alpha=0.7):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha
        self.kl_div = nn.KLDivLoss(reduction="batchmean")
        self.ce_loss = nn.CrossEntropyLoss()

    def forward(self, student_logits, teacher_logits, labels):
        student_soft = F.log_softmax(student_logits / self.temperature, dim=1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=1)

        soft_loss = self.kl_div(student_soft, teacher_soft) * (self.temperature ** 2)
        hard_loss = self.ce_loss(student_logits, labels)
        total_loss = self.alpha * soft_loss + (1.0 - self.alpha) * hard_loss
        return total_loss, soft_loss, hard_loss
```

单个批次的训练：

```python
with torch.no_grad():
    teacher_logits = teacher(images)          # 教师只推理，不更新梯度

student_logits = student(images)              # 学生需要梯度
loss, soft_loss, hard_loss = criterion(student_logits, teacher_logits, labels)

optimizer.zero_grad()
loss.backward()
optimizer.step()
```

教师加载时冻结全部参数：

```python
for param in teacher.parameters():
    param.requires_grad = False
```

#### 5.5.4 运行方式

```powershell
python 6.distillation_cnn.py
```

输出：

- `models/distilled_dog_model.pth`：学生模型；
- `results/distillation_history.png`：蒸馏训练曲线；
- `results/distillation_result.txt`：教师/学生准确率对比。

可选环境变量（方便做对比实验）：

```powershell
$env:DISTILL_EPOCHS=20
$env:DISTILL_T=2
$env:DISTILL_ALPHA=0.5
python 6.distillation_cnn.py
```

#### 5.5.5 用蒸馏后的学生模型做预测

界面支持 `--model` 参数：

```powershell
python 4.classifier_ui.py --model models/distilled_dog_model.pth
```

不加参数时仍默认加载教师模型 `models/dog_classification_model.pth`。

---

## 6. 核心技术要点

| # | 要点 | 本项目体现 |
|---|---|---|
| 1 | 训练/推理预处理必须完全一致 | 全部使用 `Resize(128) + ToTensor + ImageNet Normalize` |
| 2 | 类别名随模型保存 | checkpoint 中存 `class_names` |
| 3 | 数据清洗是训练前提 | 下载校验 + 扫描校验 + RGB 转换 + 黑图兜底 |
| 4 | 增强只用于训练集 | 训练 3 种随机增强（旋转/翻转/裁剪），测试仅 Resize |
| 5 | 固定随机种子 | 划分与训练均设 seed=42 |
| 6 | 负样本设计 | 橘猫作为干扰类，检验误判 |
| 7 | 先平均 logits 再 softmax（扩展） | 集成预测时使用，见第 9 节 |
| 8 | 界面与模型解耦 | 模型缺失时界面仍可运行 |
| 9 | 蒸馏时教师只推理 | 教师 `requires_grad=False` + `no_grad`，学生正常反向传播 |

---

## 7. 实验结果

> 以下为 2026-11-21 在本机 CPU 上实测的结果（8 类 × 300 张）。

| 项目 | 结果 |
|---|---|
| 训练集 / 测试集 | 1920 / 480（每类 240 / 60） |
| 训练轮数 | 60 |
| 测试集准确率 | **57.50%（276/480）** |
| 最佳测试准确率 | **57.50%（Epoch 60）** |
| 最后一轮准确率 | 57.50%（最佳即最后一轮） |
| 训练耗时 | 约 24.1 分钟（CPU） |

### 7.1 规模对比实验

| 配置 | 训练/测试 | 测试准确率 | 说明 |
|---|---|---|---|
| 5 类 × 150 张（历史版本） | 600 / 150 | 69.33%（104/150） | 小 CNN 在 5 类任务上的表现 |
| **8 类 × 300 张（当前主模型）** | **1920 / 480** | **57.50%（276/480）** | 类别数增加、任务更难，模型容量成为瓶颈 |
| 8 类 × 300 张 + ResNet18 | 1920 / 480 | **90.62%（435/480）** | 预训练特征对照实验 |

> 5 类结果来自旧版本，当前项目已替换为 8 类，保留该数字仅用于说明“类别数增加后难度上升”。
> 8 类任务里，金毛/橘猫/柯基的毛色非常接近，小 CNN 很容易用颜色而不是形状做判断。

> ⚠️ **方法学提醒**：本项目为简化流程，用测试集监控并挑选最佳 epoch，结果会略偏乐观。
> 严格做法是从训练集中再划出 10%~20% 作为验证集，用验证集选模型，测试集只在最后评估一次。

### 7.2 各类别准确率与混淆矩阵

| 类别 | 正确/总数 | 准确率 |
|---|---|---|
| 中华田园犬 | 35 / 60 | 58% |
| 柯基 | 41 / 60 | 68% |
| 橘猫 | 24 / 60 | 40% |
| 比格 | 36 / 60 | 60% |
| 泰迪 | 30 / 60 | 50% |
| 萨摩耶 | 44 / 60 | 73% |
| 边牧 | 39 / 60 | 65% |
| 金毛 | 27 / 60 | 45% |

混淆矩阵（行 = 真实，列 = 预测）：

| 真实\预测 | 中华田园犬 | 柯基 | 橘猫 | 比格 | 泰迪 | 萨摩耶 | 边牧 | 金毛 |
|---|---|---|---|---|---|---|---|---|
| 中华田园犬 | **35** | 3 | 3 | 3 | 2 | 0 | 3 | 11 |
| 柯基 | 3 | **41** | 1 | 8 | 0 | 3 | 1 | 3 |
| 橘猫 | 9 | 9 | **24** | 3 | 2 | 0 | 1 | 12 |
| 比格 | 3 | 9 | 2 | **36** | 1 | 0 | 6 | 3 |
| 泰迪 | 9 | 2 | 3 | 3 | **30** | 1 | 2 | 10 |
| 萨摩耶 | 1 | 4 | 2 | 2 | 1 | **44** | 3 | 3 |
| 边牧 | 4 | 1 | 2 | 8 | 0 | 3 | **39** | 3 |
| 金毛 | 10 | 4 | 11 | 3 | 2 | 1 | 2 | **27** |

**从矩阵能读出什么：**

1. **「中华田园犬」仍然是最大的“吸附类”**：金毛 11 张、泰迪 9 张、橘猫 9 张、边牧 4 张都被判成它。
   该类别本身是混血群体，毛色/体型跨度极大，模型遇到“拿不准的狗/橘色动物”就倾向归到这里。
2. **萨摩耶最容易**（73%）：白色长毛的视觉特征非常独特。
3. **金毛只有 45%**：11 张被判成橘猫、10 张被判成田园犬、4 张被判成柯基。
   金毛和橘猫都是橙黄色，模型明显在用颜色走捷径，而不是区分耳朵、脸型和毛发。
4. **橘猫只有 40%**：12 张被判成金毛、9 张被判成田园犬、9 张被判成柯基，颜色相似的类互相“吸”。
5. **泰迪 50%**：10 张被判成金毛、9 张被判成田园犬；比格 60%，其中 9 张被判成柯基；边牧 65%，其中 8 张被判成比格。

### 7.3 数据质量分析

训练前用 `results/data_preview.png` 抽查样本，训练后用 `results/misclassified.png` 汇总全部 204 张错分图。可以看到明显的标签噪声：

- 「中华田园犬」中混入了柴犬、萨摩耶、黑色犬、文字海报等；
- 「比格」中混入了博美、犬种科普信息图；
- 「泰迪」中混入了比熊、卡通插画；
- 「萨摩耶」中混入了雪纳瑞、金毛；
- 「橘猫」中混入了卡通猫、多图拼贴；
- 新增的「边牧 / 金毛 / 柯基」同样有噪声：金毛里混入橘猫和其他黄色犬，边牧里混入黑白犬，柯基里混入其他短腿犬。

这不是爬虫校验（格式/尺寸/重复）能解决的问题，需要**人工语义清洗**。当前 57.50% 里，有相当一部分错误来自测试集本身的噪声，而不只是模型能力。

> 说明：`images/` 下放的是从测试集中挑选的、模型能正确识别的 8 张样例，仅用于界面演示；整体准确率仍以 57.50% 为准，全部错例见 `results/misclassified.png`。

### 7.4 迁移学习对比实验（未集成到主流程）

作为对照，用 ImageNet 预训练的 ResNet18 做**线性探针**（冻结主干、只训练 512→8 的分类头）：

| 模型 | 测试准确率 | 说明 |
|---|---|---|
| 4 层 CNN（本项目主模型） | **57.50%（276/480）** | 从零训练，60 epoch |
| ResNet18 预训练 + 线性头 | **90.62%（435/480）** | 冻结主干，特征提取后训练线性层 |

各类别（ResNet18）：中华田园犬 53/60、柯基 55/60、橘猫 58/60、比格 55/60、泰迪 56/60、萨摩耶 53/60、边牧 54/60、金毛 51/60。

> 这组对比说明：在数据量有限、标签有噪声的细粒度任务上，**预训练特征比从头训练的小 CNN 强得多**。
> 本项目按选题要求保留 4 层 CNN 作为主模型；ResNet18 方案可作为后续升级（见第 9 节）。

### 7.5 置信度分析

- 测试集平均最大 softmax 置信度 **70.92%**；预测正确时平均 **78.35%**，预测错误时平均 **60.88%**。
  说明模型对一部分错误样本仍然过度自信，**置信度不能单独当作可信度依据**。
- `images/` 下的 8 张演示图（模型能正确识别）置信度为 **98.55%~100%**。
- 训练可视化图 `results/prediction_柯基.png` 含标题文字，属于分布外图片，置信度只有 **64.70%**（且被误判成比格），这是正常现象，不是模型故障。
- **界面默认做了温度缩放**：对 logits 除以 `T=0.7` 后再 softmax，用于让显示置信度更直观。
  - 测试集平均置信度从 **70.92% → 78.15%**；
  - **准确率仍是 57.50%，预测类别不变**；
  - 状态栏会标注“仅显示，不影响准确率”；
  - 关闭锐化：`python 4.classifier_ui.py --temperature 1.0`。
- 这不属于模型改进：温度缩放只改变显示数字，错例也会变得更“自信”。如果目标是提升准确率，**测试时增强（TTA）**更有效：多尺度/多裁剪平均可到 **60.83%**，但平均置信度会降到 62.88%。

### 7.6 知识蒸馏结果

用 `6.distillation_cnn.py` 做教师 → 学生蒸馏（教师与学生结构相同，T=4，α=0.7）：

| 模型 | 测试准确率 | 说明 |
|---|---|---|
| 教师 CNN | **57.50%（276/480）** | `3.train_cnn.py` 的输出 |
| 学生 CNN（蒸馏） | **56.67%（272/480）**，Epoch 35 | `6.distillation_cnn.py` 的最佳结果 |
| 学生最后一轮 | 56.46% | 最佳轮之后略有回落 |

各类准确率（学生）：

| 类别 | 正确/总数 | 准确率 |
|---|---|---|
| 中华田园犬 | 32 / 60 | 53% |
| 柯基 | 36 / 60 | 60% |
| 橘猫 | 30 / 60 | 50% |
| 比格 | 36 / 60 | 60% |
| 泰迪 | 30 / 60 | 50% |
| 萨摩耶 | 45 / 60 | 75% |
| 边牧 | 38 / 60 | 63% |
| 金毛 | 25 / 60 | 42% |

**结果分析：**

1. **学生没有超过教师**（低 0.83 个百分点）。这不是代码错误，而是“弱教师 + 同结构学生”的典型结果：
   教师本身只有 57.5%，软标签里没有足够可靠的新知识；学生同结构，蒸馏更接近标签平滑。
2. 主要错误类型与教师一致：金毛 13 张被判成田园犬、10 张被判成橘猫；橘猫 8 张被判成田园犬、8 张被判成柯基；说明学生学到了教师的“颜色捷径”。
3. 学生 checkpoint 约 **9 MB**（只保存 `model_state_dict` 和元信息，没有优化器状态），教师约 27 MB。
4. 加载学生模型：
   ```powershell
   python 4.classifier_ui.py --model models/distilled_dog_model.pth
   ```

**想看到蒸馏的正向收益，可以尝试：**

- 换更强的教师（如 ResNet18，8 类实测 90.62%），再蒸馏到小 CNN；
- 把学生换成更小的网络（真正的模型压缩）；
- 调整 `T` / `α`（例如 `T=2`、`α=0.5`）做对比实验，命令见 5.5.4。

**如何解读曲线**：

- 本项目曲线：训练准确率升到 **76.6%**，测试准确率停在 **57.5%**；训练损失降到 **0.64**，测试损失从约 1.4 升到 **1.58**。
- 训练准确率上升、测试准确率停滞或下降 → 过拟合；
- 训练损失下降、测试损失上升 → 同样说明过拟合；
- 正常情况：两条曲线同步上升并逐渐收敛。
- 当前 8 类任务同时存在**过拟合**和**模型容量不足**：训练集只到 76.6%，测试集更低，说明 4 层 CNN 学不出足够区分 8 个品种的特征。

**犬种任务比水果任务更难的原因**：

1. 细粒度分类：比格、泰迪、田园犬都可能有相似的毛色和体型；
2. 中华田园犬本身是混血群体，类内差异极大；
3. 百度图片存在标签噪声（插画、其他犬种、拼图）；
4. 128×128 的小 CNN 容量有限。

可选的改进方向：人工清洗数据、增大输入尺寸、ResNet18 迁移学习、类别平衡采样。

---

## 8. 常见问题与排错

| 现象 | 原因 | 解决 |
|---|---|---|
| 爬虫返回 `Forbid spider access` | Cookie 未生效或接口参数变化 | 已内置首页预热；仍失败则按 5.1.1 重新抓包 |
| 爬虫 0 张且无报错 | 响应结构变化，`data` 不是字典 | `print(type(data), data)` 看真实结构 |
| 下载图片很少 | 百度限流/链接失效 | 加大 `PAGE_INTERVAL`，换关键词，或人工补图 |
| `未找到划分后的数据集目录！` | 没运行步骤 2 | `python 2.split_data.py` |
| `未找到模型文件` | 没训练或路径不对 | 确认 `models/dog_classification_model.pth` 存在 |
| `size mismatch for classifier.0.weight` | 改了输入尺寸/类别数 | 128 输入对应 `128*8*8`；类别数必须与 `class_names` 一致 |
| 界面预测没反应 | 未选图 | 先点「选择犬类图片」 |
| 图片显示空白 | `PhotoImage` 被回收 | 已用 `self.image_label.photo = photo` |
| 中文标题显示方块 | 缺微软雅黑/黑体 | 改 `plt.rcParams['font.sans-serif']` |
| 训练准确率 100% 但测试差 | 数据太少 + 过拟合 | 增加数据、增强增强、降低模型容量 |
| `num_workers` 多进程报错 | Windows 限制 | 保持 `num_workers=0` |
| 登录失败 | 账号文件格式错误 | 保持 `admin:123456` 格式 |

---

## 9. 后续扩展方向

当前已实现教师训练、知识蒸馏和图形界面；以下为可继续扩展的方向：

1. **摄像头版界面**（`5.classifier_camera_ui.py`）
   - `cv2.VideoCapture(0)` 读取；
   - 子线程只读帧放入 `queue(maxsize=1)`，主线程用 `root.after(30, ...)` 刷新；
   - OpenCV 的 BGR 必须转 RGB；
   - 窗口关闭时 `cap.release()`。

2. **知识蒸馏**（`6.distillation_cnn.py`，已实现，见 5.5）
   - 教师模型冻结，学生模型结构相同；
   - `Loss = α·T²·KL(softmax(student/T) ‖ softmax(teacher/T)) + (1-α)·CE`
   - 本项目采用标准写法：`alpha=0.7`、`T=4`；可通过 `DISTILL_T`、`DISTILL_ALPHA` 环境变量做对比实验。
   - 后续可尝试真正的模型压缩（把学生换成更小的网络），或调整 T/α 观察学生准确率变化。

3. **集成预测界面**（`7.distillation_predictor.py`）
   - 教师与学生 logits 取平均后再 softmax；
   - 加载时必须校验两个模型的类别顺序一致。

4. **模型升级（收益最大）**
   - `torchvision.models.resnet18(weights='DEFAULT')` 迁移学习，输入改 224；
   - 本项目实测：8 类任务上，冻结主干 + 线性分类头即可达到 **90.62%（435/480）**，比自建 CNN 高 33 个百分点；
   - 实现上只需在 `3.train_cnn.py` 里按 `model_type` 构建不同模型，并在 checkpoint 中记录模型类型，界面据此选择网络结构。

5. **数据增强升级**
   - ColorJitter、RandomAffine、MixUp/CutMix；
   - 对细粒度任务，随机裁剪比例可适当收紧。

6. **工程化**
   - 把 `DogCNN` 抽到 `model.py`（数字开头的脚本不能互相 import，可用 `importlib` 动态导入）；
   - 预处理参数抽成全局常量；
   - `requirements.txt` 已提供，可直接固定版本。

---

## 10. 与原水果项目的对应关系

| 原项目 | 本项目 | 说明 |
|---|---|---|
| 5 类水果 + 手机负样本 | 7 种犬 + 橘猫负样本 | 任务同构 |
| FruitCNN | DogCNN | 结构完全相同 |
| `fruit_classification_model.pth` | `dog_classification_model.pth` | 路径约定一致 |
| `6.distillation_cnn.py` | `6.distillation_cnn.py` | 标准 α·T²·KL + (1-α)·CE |
| 7 个脚本 | 4 个核心脚本 + 1 个蒸馏脚本 | 摄像头/集成留作扩展 |
| 百度爬虫 | 百度爬虫（增加 Cookie 预热） | 接口行为变化，已适配 |
| 128×128 输入 | 128×128 输入 | 保持一致 |

---

## 附录：命令速查

```powershell
# 环境
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install opencv-python pillow numpy matplotlib requests tqdm

# 1. 采集
python 1.download_data.py

# 2. 划分
python 2.split_data.py

# 3. 训练
python 3.train_cnn.py

# 4. 界面（教师模型）
python 4.classifier_ui.py

# 5. 知识蒸馏（可选）
python 6.distillation_cnn.py

# 6. 用学生模型做预测
python 4.classifier_ui.py --model models/distilled_dog_model.pth

# 账号
admin / 123456
user  / 123456

# 备份模型（重新训练前）
Copy-Item models\dog_classification_model.pth models\dog_classification_model_bak.pth
Copy-Item models\distilled_dog_model.pth models\distilled_dog_model_bak.pth
```