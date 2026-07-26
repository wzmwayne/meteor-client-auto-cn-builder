import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")

def load_translations():
    path = os.path.join(SCRIPT_DIR, "translations.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    filtered = {}
    for k, v in raw.items():
        if v is None:
            continue
        if len(k) <= 2:
            continue
        filtered[k] = v
    return filtered, raw

def replace_literals(content, translations):
    def replace_match(m):
        inner = m.group(1)
        if inner in translations:
            return '"' + translations[inner] + '"'
        return m.group(0)

    # Match Java string literals: "..."
    # Handles escape sequences and skips text blocks
    pattern = re.compile(r'"((?:[^"\\]|\\.)*)"')
    return pattern.sub(replace_match, content)

def inject_utils(java_path, translations_size):
    with open(java_path, encoding="utf-8") as f:
        content = f.read()

    # Add Gson and InputStreamReader imports after the last org.jetbrains import
    import_marker = "import org.jetbrains.annotations.Range;"
    extra_imports = "import com.google.gson.Gson;\nimport com.google.gson.reflect.TypeToken;\nimport java.io.InputStreamReader;"
    if import_marker in content and "import com.google.gson.Gson;" not in content:
        content = content.replace(import_marker, import_marker + "\n" + extra_imports)

    # Add translation infrastructure after private Utils() {}
    utils_constructor = "    private Utils() {\n    }"
    translation_code = """
    private static Map<String, String> TRANSLATIONS = null;
    private static final Gson GSON = new Gson();

    public static void loadTranslations() {
        TRANSLATIONS = new HashMap<>();
        try (InputStream in = Utils.class.getResourceAsStream("/assets/meteor-client/lang/zh_cn_full.json")) {
            if (in != null) {
                Map<String, String> map = GSON.fromJson(new InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8), new TypeToken<Map<String, String>>() {}.getType());
                if (map != null) TRANSLATIONS.putAll(map);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static String tr(String text) {
        if (TRANSLATIONS == null) loadTranslations();
        String translated = TRANSLATIONS.get(text);
        return translated != null ? translated : text;
    }
"""
    if utils_constructor in content and "private static Map<String, String> TRANSLATIONS" not in content:
        before = content.index(utils_constructor) + len(utils_constructor)
        content = content[:before] + translation_code + content[before:]

    # Hijack nameToTitle
    name_to_title = "public static String nameToTitle(String name) {\n        return Arrays.stream(name.split(\"-\")).map(StringUtils::capitalize).collect(Collectors.joining(\" \"));\n    }"
    hijacked = "public static String nameToTitle(String name) {\n        String title = Arrays.stream(name.split(\"-\")).map(StringUtils::capitalize).collect(Collectors.joining(\" \"));\n        return tr(title);\n    }"
    if name_to_title in content and "return tr(title)" not in content:
        content = content.replace(name_to_title, hijacked)

    with open(java_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    java_dir = os.path.join(PROJECT_DIR, "src", "main", "java")
    if not os.path.isdir(java_dir):
        # Maybe running from meteor-client checkout (not builder repo)
        java_dir = "src/main/java"
        if not os.path.isdir(java_dir):
            print("ERROR: Cannot find src/main/java. Run this script from the meteor-client checkout.", file=sys.stderr)
            sys.exit(1)

    translations, raw = load_translations()
    print(f"Loaded {len(translations)} translatable keys (filtered from {len(raw)} total)")

    replaced_total = 0
    files_modified = 0
    utils_modified = False

    for root, dirs, files in os.walk(java_dir):
        for fname in files:
            if not fname.endswith(".java"):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8") as f:
                original = f.read()

            modified = replace_literals(original, translations)
            if modified != original:
                replaced = sum(1 for k in translations if f'"{k}"' in original and f'"{k}"' not in modified)
                replaced_total += replaced
                files_modified += 1

            with open(path, "w", encoding="utf-8") as f:
                f.write(modified)

            if fname == "Utils.java":
                inject_utils(path, len(translations))
                utils_modified = True

    print(f"Replaced strings in {files_modified} files")
    print(f"Total replacements: ~{replaced_total}")
    if utils_modified:
        print("Injected translation infrastructure + nameToTitle hijack in Utils.java")

if __name__ == "__main__":
    main()
