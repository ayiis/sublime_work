import sublime
import sublime_plugin
import json


class format_jsonCommand(sublime_plugin.TextCommand):

    def run(self, edit):

        # 如果有选中文本，就使用选中的文本
        target_text = selected_lines = self.view.substr(self.view.sel()[0])
        is_whole_file = bool(selected_lines == "")

        # 是否处理整个文件
        if is_whole_file:
            target_region = sublime.Region(0, self.view.size())
            self.view.sel().add(target_region)
            file_content = self.view.substr(target_region)
            target_text = file_content
        else:
            # target_region = sublime.Region(self.view.sel()[0])
            target_region = self.view.sel()[0]

        # 只能处理正常的json
        data_json = json.loads(target_text)
        res_text = json.dumps(data_json, sort_keys=True, indent=4, separators=(", ", ": "), ensure_ascii=False)

        # insert 在换行时会自动插入空格，此处关闭 auto_indent
        auto_indent = self.view.settings().get("auto_indent")
        if auto_indent:
            self.view.settings().set("auto_indent", False)

        # self.view.run_command("insert", {"characters": res_text})
        self.view.replace(edit, target_region, res_text)

        if auto_indent:
            self.view.settings().set("auto_indent", auto_indent)
