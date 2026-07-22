# Meteor Client 中文构建器

从 [MeteorDevelopment/meteor-client](https://github.com/MeteorDevelopment/meteor-client) master 分支自动构建中文汉化版。

## 工作流程

1. 手动触发 GitHub Actions → 检出上游 master
2. 应用 `patches/*.patch`（修改 6 个 Java 文件添加翻译支持）
3. 复制 CJK 字体（WenQuanYi Zen Hei 完整版）
4. 运行 `scripts/translate.py`（查表 → API fallback）
5. Gradle 构建，上传 JAR 为 Artifact
6. 更新 `scripts/translations.json` 回仓库（持久化 API 翻译结果）

## 手动触发

```bash
gh workflow run build.yml -R wzmwayne/meteor-client-auto-cn-builder
```

支持参数：
- `build_number` — 构建号（默认自动生成）
- `upstream_ref` — 上游分支/tag/commit（默认 master）
- `skip_sync` — 跳过翻译回写（true/false）

## 文件结构

| 路径 | 说明 |
|------|------|
| `patches/*.patch` | 对上游 6 个 Java 文件的侵入式修改 |
| `scripts/translate.py` | 翻译脚本：硬编码翻译表 → Google API fallback |
| `scripts/translations.json` | 3213 条硬编码翻译（中英双语） |
| `fonts/WenQuanYi Zen Hei.ttf` | 完整文泉驿正黑字体（17MB，包含全部字形防乱码） |
| `.github/workflows/build.yml` | 构建工作流 |

## 修改的 Java 文件

- `Utils.java` — 翻译映射表、`tr()`/`trIfPresent()` 方法
- `MeteorClient.java` — 加载翻译文件时机
- `Command.java` — 命令标题/描述包装
- `MeteorGuiTheme.java` — GUI 文本包装
- `Fonts.java` — 添加 CJK 内置字体，设为默认
- `Font.java` — CJK 字形范围（U+4E00–U+9FFF）
