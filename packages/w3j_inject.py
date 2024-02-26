import sublime
import sublime_plugin
import os
import re
import uuid
"""
    按顺序匹配是最理想的状态，但是过程的每一步不一定有，所以需要可以跳过，复杂度高，那还不如无序执行
"""

str_insert_map = {
    r'''endglobals''': {
        "before": "xaaaabefore endglobals",
        "after": "xaaaaafter endglobals",
    },
    r'''function\s+main\s+takes\s+nothing\s+returns\s+nothing''': {
        "before": "xaaaabefore main",
        "after": "xaaaaafter main",
    },
}
str_delete_map = [
    r'''call\s+SetAmbientNightSound\("DalaranNight"\)''',
    r'''call\s+SetMapMusic\("Music", true, 0\)''',
]
str_replace_map = {
    r'''function\s+InitAllyPriorities\s+takes\s+nothing\s+returns\s+nothing''': '''function nothing_to_do_%s takes nothing returns nothing''' % (uuid.uuid4().hex),
}


class w3j_injectCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        file_name = self.view.file_name()
        if not (file_name and os.path.exists(file_name)):
            return

        content = work(infile=file_name)

        target_region = sublime.Region(0, self.view.size())
        self.view.replace(edit, target_region, content)


def work(infile):

    output_buffer = []
    output_strings = []

    with open(infile, "r") as rf:

        for line_no, line in enumerate(rf):

            line_low = line.strip().lower()

            # 删除
            key_del = next((re_key for re_key in str_delete_map if re.match(re_key, line_low, re.I)), None)
            if key_del:
                output_strings.append("DEL %sL: %s%s" % (line_no, key_del[:60], len(key_del) > 60 and ".." or ""))
                continue

            # 替换
            key_replace = next((re_key for re_key in str_replace_map if re.match(re_key, line_low, re.I)), None)
            if key_replace:
                output_strings.append("REPLACE %sL: %s%s" % (line_no, key_replace[:60], len(key_replace) > 60 and ".." or ""))
                output_buffer.append(str_replace_map[key_replace])
                output_buffer.append("\n")
                continue

            # 插入
            key_insert = next((re_key for re_key in str_insert_map if re.match(re_key, line_low, re.I)), None)
            if key_insert:
                output_strings.append("INSERT %sL: %s%s" % (line_no, key_insert[:60], len(key_insert) > 60 and ".." or ""))
                output_buffer.append(str_insert_map[key_insert]["before"])
                output_buffer.append("\n")
                output_buffer.append(line)
                output_buffer.append("\n")
                output_buffer.append(str_insert_map[key_insert]["after"])
                output_buffer.append("\n")
                continue

            output_buffer.append(line)

    print("\r\n".join(output_strings))
    return "".join(output_buffer)
