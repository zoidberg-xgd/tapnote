# TapNote 功能特性

TapNote 是一个功能丰富的自托管发布平台，支持 Markdown 编辑、段落评论、数据迁移等功能。

## 🆕 核心功能

### 1. 评论和点赞系统
- **段落评论功能**：集成了 [ParaNote](https://github.com/zoidberg-xgd/paranote) 评论系统
- **段落级评论**：支持在文章的任何段落添加评论
- **点赞功能**：支持对评论进行点赞
- **模糊定位**：即使文章内容更新，评论也能自动定位到正确段落
- **管理员功能**：支持管理员删除评论

### 2. 数据迁移功能
- **导出功能**：可以将所有笔记导出为 JSON 格式
- **导入功能**：支持从 JSON 文件恢复笔记
- **数据备份**：方便进行数据备份和迁移

### 3. PythonAnywhere 部署支持
- **自动化部署脚本**：`deploy_pa.sh` 一键部署到 PythonAnywhere
- **自动续期脚本**：`scripts/renew_pa.py` 自动延续免费 Web 应用有效期
- **GitHub Actions 集成**：支持自动续期工作流
- **详细部署文档**：`DEPLOY_PYTHONANYWHERE.md` 和 `UPDATE_PYTHONANYWHERE.md`

### 4. 测试和 CI/CD
- **测试脚本**：`run_tests.sh` 支持测试和覆盖率报告
- **GitHub Actions**：自动化测试工作流
- **测试覆盖**：包含单元测试和集成测试

### 5. 工具脚本
- **txt2tapnote**：将文本文件批量导入为 TapNote 笔记
- **renew_pa**：PythonAnywhere 自动续期工具

### 6. 管理功能
- **Django Admin**：支持在管理后台管理笔记和评论
- **初始管理员设置**：首次运行时自动创建管理员账户

### 7. 国际化支持
- **中文 README**：提供完整的中文文档 `README_CN.md`

## 🔧 改进和优化

- **UI 优化**：修复了文字重叠和语言不一致问题
- **代码质量**：添加了测试覆盖和代码规范
- **文档完善**：补充了部署和使用文档
- **错误处理**：改进了错误处理和用户体验

## 📊 功能对比

| 功能 | TapNote |
|------|---------|
| Markdown 编辑 | ✅ |
| 即时发布 | ✅ |
| 段落级评论 | ✅ |
| 评论点赞 | ✅ |
| 数据迁移 | ✅ |
| PythonAnywhere 部署 | ✅ |
| 测试框架 | ✅ |
| CI/CD | ✅ |
| 中文文档 | ✅ |
| Django Admin | ✅ |

## 🚀 使用场景

TapNote 适合以下场景：
- **个人博客**：快速发布 Markdown 文章
- **团队协作**：通过评论系统进行讨论
- **内容备份**：使用数据迁移功能备份内容
- **自托管发布**：完全掌控自己的内容

## 📝 许可证

使用 [MIT License](LICENSE)。

## 🙏 致谢

- 灵感来自 [Telegra.ph](https://telegra.ph)
- 最初基于 [vorniches/tapnote](https://github.com/vorniches/tapnote) 的概念
- 评论系统由 [ParaNote](https://github.com/zoidberg-xgd/paranote) 提供支持
