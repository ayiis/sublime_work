# sublime_work

工欲善其事必先利其器

## 配置

### 常用安装的 package（Install Package）

```text
Package Control
Markdown Extended
Jsformat
CSS Format
PowerShell
LSP
LSP-pyright (需要安装nodejs环境)
SublimeLinter
SublimeLinter-flake8
Jade (已不维护)
```

### Sublime Text 全局配置（Preference: Settings）

文件名: `Preferences.sublime-settings`

```js
{
	"color_scheme": "Solarized (light).sublime-color-scheme",
	"default_line_ending": "unix",
	"enable_hexadecimal_encoding": false,
	"ensure_newline_at_eof_on_save": false,
	"show_project_first": true,
	"folder_exclude_patterns":
	[
		".svn",
		".git",
		".hg",
		"CVS",
		"node_modules",
		"__pycache__",
		".vscode"
	],
	"font_face": "fantasque sans mono",

	"mini_diff": true,
	"show_git_status_in_status_bar": true,
	"show_git_status": true,

	"font_size": 15,
	"highlight_line": true,
	"index_files": false,
	"overlay_scroll_bars": "enabled",
	"show_definitions": false,
	"tab_size": 4,
	"theme": "Default.sublime-theme",
	"translate_tabs_to_spaces": true,
	"trim_trailing_white_space_on_save": true,
	"update_check": false,
}
```

### pyright 配置（Preference: LSP-pyright Settings）

文件名: `LSP-pyright.sublime-settings`

```js
{
    "settings": {
        "python.analysis.diagnosticSeverityOverrides": {
            "reportMissingImports": false,
        },
    },
}
```

### flake8 配置（Preference: SublimeLinter Settings）

文件名: `SublimeLinter.sublime-settings`

```js
{
    "linters": {
        "flake8": {
            "args": ["--extend-ignore", "E501"],
        },
    },
}
```

## 插件

### 右键菜单

文件名: `Context.sublime-menu`

```js
[
    {
        "id": "aycommand",
        "caption": "aycommand(Super+J)",
        "children": [{
            "id": "format_json",
            "caption": "format_json(+1)",
            "command": "format_json",
        }, {
            "id": "align_multi_lines",
            "caption": "align_multi_lines(+2)",
            "command": "align_multi_lines",
        }, {
            "id": "line_with_quote",
            "caption": "line_with_quote(+3)",
            "command": "line_with_quote",
        }, {
            "id": "format_odps",
            "caption": "format_odps(+4)",
            "command": "format_odps",
        }, {
            "id": "super_decode",
            "caption": "super_decode(+5)",
            "command": "super_decode",
        }, {
            "id": "w3j_inject",
            "caption": "w3j_inject(+9)",
            "command": "w3j_inject",
        }]
    }
]
```

### 快捷键（Key Bindings）

文件名: `Default (Windows).sublime-keymap`

不同操作系统下的名字不一样，例如当前Win10下是 `Windows`, MacOS下是 `OSX`

```js
[
    {"keys": ["ctrl+j", "ctrl+1"], "command": "format_json"},
    {"keys": ["ctrl+j", "ctrl+2"], "command": "align_multi_lines"},
    {"keys": ["ctrl+j", "ctrl+3"], "command": "line_with_quote"},
    {"keys": ["ctrl+j", "ctrl+4"], "command": "format_odps"},
    {"keys": ["ctrl+j", "ctrl+5"], "command": "super_decode"},
    {"keys": ["ctrl+j", "ctrl+9"], "command": "w3j_inject"},
]
```

### 自己开发 Sublime 插件

1. 使用 `class xxxxCommand(sublime_plugin.TextCommand):` 来注册1个 Sublime 的 `xxxx` 命令

2. 把插件的py文件放到与上述的配置、右键菜单等放在同一目录下（通常是 `$(SublimeRoot)\Data\Packages\User`），Sublime 将自动读取

例如将如下代码保存为 `$(SublimeRoot)\Data\Packages\User\line_with_quote.py`

```js
import sublime
import sublime_plugin

class line_with_quoteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        all_lines = self.view.substr(self.view.sel()[0])
        all_lines = all_lines.split("\n")
        res_line = str([x.strip() for x in all_lines if x.strip()])[1:-1]
        self.view.replace(edit, self.view.sel()[0], res_line)
```

保存后，Sublime 将自动注册1个新的命令 `line_with_quote`

在 Sublime 的命令行执行 `view.run_command("line_with_quote")` 即可执行注册的命令

为命令配置快捷键后，通过快捷键即可直接调用该命令
