# TapNote

[English](README.md) | [中文](README_CN.md)

> 本项目 Fork 自 [vorniches/tapnote](https://github.com/vorniches/tapnote)

TapNote 是一个极简的自托管发布平台，灵感来自 Telegra.ph，专注于基于 Markdown 的即时内容创作。它提供了无干扰的写作体验和即时发布功能，非常适合快速记录笔记、撰写博客文章或分享文档。

> 查看关于创建 TapNote 的报告：[dev.to](https://dev.to/vorniches/building-self-hosted-telegraph-in-1-prompt-and-3-minutes-2li2) 或 [YouTube](https://youtu.be/ArPGGaG5EU8)。

![Demo](media/demo.gif)

## 功能特点

- **极简写作体验**
  - 干净、无干扰的 Markdown 编辑器
  - 无需注册账号
  - 一键即时发布
  - 支持完整的 Markdown 语法
  - 自托管：完全掌控您的内容

- **内容管理**
  - 每篇文章拥有唯一 URL
  - 通过安全令牌进行编辑
  - 正确渲染所有 Markdown 元素
  - 支持图片和代码片段

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/zoidberg-xgd/tapnote.git
cd tapnote
```

2. 使用 Docker 启动应用：
```bash
chmod +x setup.sh
./setup.sh
```

3. 访问 TapNote：`http://localhost:9009`

## 示例

```Markdown
# 标题 1
这里是一些段落文本。

![图片](https://themepreview.home.blog/wp-content/uploads/2019/07/boat.jpg)

## 标题 2
另一段包含 **粗体**、*斜体* 和 ~~删除线~~ 的文本。

### 标题 3
1. 有序列表项
2. 另一个有序列表项

'```python
# 一些 Python 代码片段
def greet(name):
    return f"Hello, {name}!"
```'

#### 标题 4
引用块：
> 这是一个引用块！

- 无序子列表项
- 无序子列表项

#### 表格示例
| 列 A | 列 B |
|----------|----------|
| 单元格 1A  | 单元格 1B  |
| 单元格 2A  | 单元格 2B  |

https://youtu.be/vz91QpgUjFc?si=6nTE2LeukJprXiw1
```

> 注意：为了正确渲染代码示例，请移除 `'` 符号。

## 测试

TapNote 包含覆盖所有主要组件的全面单元测试和集成测试。

### 运行测试

```bash
# 使用 Django 测试运行器
python manage.py test

# 使用测试脚本
./run_tests.sh

# 生成覆盖率报告
./run_tests.sh --coverage

# 更多详情请参阅 TESTING.md
```

### 测试覆盖率

- ✅ 模型测试（笔记创建、验证、时间戳）
- ✅ 视图测试（所有端点和边界情况）
- ✅ 辅助函数测试（Markdown 处理、YouTube 嵌入）
- ✅ OpenAI 集成测试
- ✅ 端到端工作流测试

## 贡献

欢迎提交 Pull Request。对于重大更改，请先开 issue 讨论您想要更改的内容。

## 许可证

[MIT License](LICENSE)

## 致谢

- 灵感来自 [Telegra.ph](https://telegra.ph)
- 使用 Django 和 Tailwind CSS 构建
- 使用 [Prototype](https://github.com/vorniches/prototype)、[snap2txt](https://github.com/vorniches/snap2txt) 和 [Cursor](https://cursor.so) 在几分钟内启动
- 使用 Google Fonts 的 Space Mono 字体

## 支持

- 创建 issue 报告 bug 或请求新功能
- 如果您觉得有用，请给仓库点个 Star
- Fork 仓库以贡献代码或创建您自己的版本
