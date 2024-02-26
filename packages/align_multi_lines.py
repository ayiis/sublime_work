import sublime
import sublime_plugin
import re


class align_multi_linesCommand(sublime_plugin.TextCommand):

    spec_chars = ["=", "#", "//", "COMMENT", ":", "--"]
    sql_word = ["STRING", "DOUBLE", "BIGINT"]

    def run(self, edit):
        all_lines_raw = self.view.substr(self.view.sel()[0])
        all_lines = all_lines_raw.split("\n")
        if not all_lines:
            return

        for spec_char in self.spec_chars:

            # 判断是否每一行都有同样的分隔符号
            bad = next((x for x in all_lines if (x.strip() and spec_char not in x.upper())), None)
            if bad:
                continue

            all_lines_split = [re.split(spec_char, line, 1, re.I) for line in all_lines]

            todo_pairs = []
            for i, line in enumerate(all_lines_split):

                # 跳过空行
                if len(line) == 1:
                    all_lines[i] = line[0]
                    continue

                first = line[0].rstrip()
                last = line[1].lstrip()

                # 进一步加工 SQL 建表语句，向前找一个关键字
                if spec_char == "COMMENT":
                    first, aa = first.rsplit(" ", 1)
                    first = first.rstrip()
                    if aa.upper() in self.sql_word:
                        prev_char = aa.upper()

                    todo_pairs.append([first, prev_char + " " + spec_char + " " + last])

                else:
                    todo_pairs.append([first, spec_char + " " + last])

            max_len = max([len(x[0]) for x in todo_pairs])
            for i, pair in enumerate(todo_pairs):
                if len(all_lines_split[i][0]) == 1:
                    continue
                all_lines[i] = pair[0] + " " * (max_len + 1 - len(pair[0])) + pair[1]

        # # insert 在换行时会自动插入空格，此处关闭 auto_indent
        # auto_indent = self.view.settings().get("auto_indent")
        # if auto_indent:
        #     self.view.settings().set("auto_indent", False)

        target_region = self.view.sel()[0]
        # self.view.run_command("insert", {"characters": "\n".join(all_lines)})
        target_result = "\n".join(all_lines)
        if target_result != all_lines_raw:
            self.view.replace(edit, target_region, target_result)

        # if auto_indent:
        #     self.view.settings().set("auto_indent", auto_indent)
