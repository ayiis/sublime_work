import sublime
import sublime_plugin


class line_with_quoteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        all_lines = self.view.substr(self.view.sel()[0])
        all_lines = all_lines.split("\n")
        # all_lines = ["'%s'" % line.strip() for line in all_lines if line]
        # self.view.run_command("insert", {"characters": ",".join(all_lines)})
        res_line = str([x.strip() for x in all_lines if x.strip()])[1:-1]
        self.view.replace(edit, self.view.sel()[0], res_line)
