# 桌面小狗（Desktop Pet）

一个运行在 Windows 上的透明桌面宠物。

程序使用 **PyQt5 + QtWebEngine** 创建一个无边框、透明、始终置顶的窗口，并通过 `index.html` 中的纯 HTML/CSS/JS 渲染小狗和动画。

## 功能

- 无边框、透明背景、始终置顶
- 不在 Windows 任务栏显示图标
- 待机时轻微呼吸起伏
- 鼠标移入时轻轻放大
- 点击时跳跃
- 按住鼠标左键可拖动到桌面任意位置
- 右键菜单：
  - **打个招呼**：小狗头顶显示文字气泡
  - **退出**：关闭程序

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `pet.py` | PyQt5 主程序，负责窗口、拖拽和右键菜单 |
| `index.html` | 小狗界面和 CSS/JS 动画 |
| `dog.png` | 透明背景的小狗图片，需与 `pet.py` 放在同一目录 |

## 环境要求

- Windows 10 / 11
- Python 3.8 及以上（本项目在 Python 3.13 下测试）
- `PyQt5`
- `PyQtWebEngine`

## 安装依赖

打开终端，进入项目目录后执行：

```bash
python -m pip install PyQt5 PyQtWebEngine
```

## 运行

```bash
python pet.py
```

如果不想显示控制台窗口，可以使用：

```bash
pythonw pet.py
```

程序启动后，小狗会出现在屏幕右下角。

## 使用方式

| 操作 | 效果 |
| --- | --- |
| 鼠标左键拖动 | 移动小狗到桌面任意位置 |
| 鼠标左键单击 | 小狗跳跃 |
| 鼠标右键 | 打开“打个招呼 / 退出”菜单 |

## 说明

- 需要确保 `dog.png` 是一张透明背景的 PNG 图片。
- 如果双击 `pet.py` 后窗口一闪而过，请在终端中运行 `python pet.py` 查看具体错误信息。
- 本项目已配置 `.gitignore`，不会提交 `__pycache__`、`.vscode`、`.env` 等文件。
