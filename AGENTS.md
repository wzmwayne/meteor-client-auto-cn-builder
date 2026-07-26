# AGENTS.md — Meteor Client 中文构建器

本仓库 **不是** Meteor Client 源码，而是一个 CI 构建器：对上游 `MeteorDevelopment/meteor-client` 打补丁、翻译、构建，产出汉化 JAR。

## 关键结构

| 路径 | 说明 |
|------|------|
| `patches/font/*.patch` **(4 个)** | 字体渲染补丁（CJK 字形、图集、基线补偿） |
| `patches/translate/*.patch` **(3 个)** | 运行时翻译补丁（`Utils.patch` + `MeteorGuiTheme.patch` + `WMeteorModule.patch`） |
| `scripts/translate.py` | 扫描 Java 源码提取英文字符串 → 查 `translations.json` → API fallback → 输出 `zh_cn_full.json` |
| `scripts/replace_strings.py` | 编译期替换脚本：用 `translations.json` 替换源码字面量 + 劫持 `nameToTitle()` |
| `scripts/translations.json` | 3215 条硬编码翻译表；3 条 null（`"+"`、`"-"`、`"{} {}"`）表示保持原文 |
| `fonts/WenQuanYi Micro Hei.ttf` | 文泉驿米黑字体（4.5MB，包含全部字形防乱码） |
| `.github/workflows/build.yml` | 唯一构建方式 |

## 构建方式（仅 GitHub Actions 手动触发）

```bash
gh workflow run build.yml -R wzmwayne/meteor-client-auto-cn-builder
```

参数：
- `mode` — 构建模式（`full` / `patch-only` / `replace-string` / `compile-original`，默认 `full`）
- `upstream_ref` — 上游分支/tag/commit（默认 `master`）
- `build_number` — 构建号（默认 `cn-$(date +%Y%m%d%H%M)`）
- `skip_sync` — `true` 跳过翻译回写（默认 `false`）

## 各模式流程

### `full`（全流程汉化——默认）

```
font/ 补丁 → translate/ 补丁 → API 翻译 → ./gradlew build → 上传 JAR → 回写翻译
```

### `patch-only`（字体补丁 + 裸编译）

```
font/ 补丁 → ./gradlew build → 上传 JAR
```

产出：英文 Meteor + CJK 字体渲染能力。

### `replace-string`（编译期替换）

```
font/ 补丁 → API 翻译 → replace_strings.py → ./gradlew build → 上传 JAR → 回写翻译
```

`replace_strings.py` 做两件事：
1. 扫描所有 `.java`，精确匹配 `translations.json` 英文字面量 → 替换为中文
2. 注入 `Utils.java`：`TRANSLATIONS` 映射表 + `tr()` + 劫持 `nameToTitle()` 返回 `tr(title)`

跳过 `translate/` 补丁，因为 `nameToTitle` 劫持已覆盖模块标题/设置名。

### `compile-original`（纯上游编译）

```
./gradlew build → 上传 JAR
```

产出：完全原版英文 Meteor。

## 总览

| 模式 | font/ 补丁 | translate/ 补丁 | API 翻译 | 编译期替换 | 回写 |
|---|:---:|:---:|:---:|:---:|:---:|
| **full** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **patch-only** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **replace-string** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **compile-original** | ❌ | ❌ | ❌ | ❌ | ❌ |

## 补丁说明

### `patches/font/`（4 个）

- **Fonts.patch** — 内置 WenQuanYi Micro Hei 并设为默认
- **Font.patch** — CJK 字形范围 U+4E00–U+9FFF
- **AtlasSize.patch** — 纹理图集从 2048→4096 以容纳 CJK 字形
- **FontBaseline.patch** — 统一不同字体间的基线

### `patches/translate/`（3 个）

- **Utils.patch** — 添加 `TRANSLATIONS` 映射表 + `loadTranslations()` + `tr()`/`trIfPresent()`，懒加载翻译文件
- **MeteorGuiTheme.patch** — 在 `label()`、`button()`、`tooltip()`、`window()`、`section()` 等 GUI 组件中调用 `trIfPresent()`
- **WMeteorModule.patch** — 模块标题 `Utils.trIfPresent(title)`

## 其他注意事项

- 补丁紧跟上游 master，上游代码变更可能导致 `git apply` 失败，需手动修复
- 翻译脚本扫描 `src/main/java/**/*.java`（约 949 个文件），每次运行约 1-3 分钟
- `translations.json` 中 3 个条目值为 `null`（`"+"`、`"-"`、`"{} {}"`），表示保持原文不翻译，不要改动
- 本仓库所有代码由 AI 生成（见 `scripts/CHANGES.md`）
