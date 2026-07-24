# AGENTS.md — Meteor Client 中文构建器

本仓库 **不是** Meteor Client 源码，而是一个 CI 构建器：对上游 `MeteorDevelopment/meteor-client` 打补丁、翻译、构建，产出汉化 JAR。

## 关键结构

| 路径 | 说明 |
|------|------|
| `patches/*.patch` **(7 个)** | 对上游文件的补丁（翻译、字体、字形） |
| `scripts/translate.py` | 扫描 Java 源码提取英文字符串 → 查 `translations.json` → API fallback → 输出 `zh_cn_full.json` |
| `scripts/translations.json` | 3215 条硬编码翻译表，API 新增的翻译会自动写回此文件；3 条 null（`"+"`、`"-"`、`"{} {}"`）表示保持原文 |
| `fonts/WenQuanYi Micro Hei.ttf` | 文泉驿米黑字体（4.5MB，包含全部字形防乱码） |
| `.github/workflows/build.yml` | 唯一构建方式 |

## 构建方式（仅 GitHub Actions 手动触发）

```bash
gh workflow run build.yml -R wzmwayne/meteor-client-auto-cn-builder
```

参数：
- `upstream_ref` — 上游分支/tag/commit（默认 `master`）
- `build_number` — 构建号（默认 `cn-$(date +%Y%m%d%H%M)`）
- `skip_translate` — `true` 跳过翻译，仅打补丁+编译（默认 `false`）
- `skip_sync` — `true` 跳过翻译回写（默认 `false`）

## CI 流程

1. 检出 builder 仓库 + 上游 meteor-client（`master`）
2. `cp patches/*.patch scripts/ fonts/` 到上游目录
3. `git apply *.patch` 打补丁（`skip_translate=true` 时跳过 `Utils.patch`、`MeteorGuiTheme.patch`、`WMeteorModule.patch`）
4. `pip install deep-translator -q && python3 scripts/translate.py`（`skip_translate=true` 时跳过）
5. `./gradlew build -Pbuild_number=... --no-daemon`（JDK 25，非 LTS）
6. 上传 `meteor-client/build/libs/*.jar`（保留 30 天）
7. 自动提交 `translations.json` 回本仓库（除非 `skip_sync=true` 或 `skip_translate=true`）

## 补丁概况（7 个）

- **翻译核心**: `Utils.patch`（添加 `TRANSLATIONS` 映射表 + `loadTranslations()` + `tr()`/`trIfPresent()`，懒加载翻译文件）+ `MeteorGuiTheme.patch` + `WMeteorModule.patch`（在 `label()`、`button()`、`tooltip()`、`window()`、`section()`、`WMeteorModule` 标题等 GUI 组件中调用 `trIfPresent()`，覆盖全部 UI 文本）
- **字体**: `Fonts.patch`（内置 WenQuanYi Micro Hei 并设为默认）、`Font.patch`（CJK 字形范围 U+4E00–U+9FFF）、`AtlasSize.patch`（纹理图集从 2048→4096 以容纳 CJK 字形）、`FontBaseline.patch`（统一不同字体间的基线）
- 补丁紧跟上游 master，上游代码变更可能导致 `git apply` 失败，需手动修复
- 翻译脚本扫描 `src/main/java/**/*.java`（约 949 个文件），每次运行约 1-3 分钟
- `translations.json` 中 3 个条目值为 `null`（`"+"`、`"-"`、`"{} {}"`），表示保持原文不翻译，不要改动
- 本仓库所有代码由 AI 生成（见 `scripts/CHANGES.md`）
