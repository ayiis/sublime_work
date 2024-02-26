# sublime_work

工欲善其事必先利其器


### Sublime Text 全局配置

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

### 常用安装的 package

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

### pyright 设置

```js
{
    "settings": {
        "python.analysis.diagnosticSeverityOverrides": {
            "reportMissingImports": false,
        },
    },
}
```
