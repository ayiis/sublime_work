import sublime
import sublime_plugin
import os


class super_decodeCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        file_name = self.view.file_name()
        if not (file_name and os.path.exists(file_name)):
            return

        worker = Worker()
        content = worker.decode(infile=file_name)

        # target_region = self.view.sel()[0]
        target_region = sublime.Region(0, self.view.size())
        self.view.replace(edit, target_region, content)


"""
    用于处理混合编码的脚本文件，例如 j 文件
    只适用于 中文
    原理：
        按行读取处理
            所以如果同一行有不同的编码，那就白给
        尝试各种编码解析
            如果解析出来的字符在 字母、数字、英文特殊符号、简体中文+繁体中文+中文特殊符号 的白名单内，直接输出解析结果
            如果解析出来的字符超出白名单，则尝试下一种编码，直到符合
            如果都没有符合的，那就强制 UTF8
        输出所有结果

    ddd = set(['【', '】', '〔', ...]) - set([chr(x) for x in range(30, 128)])

    https://github.com/shengdoushi/common-standard-chinese-characters-table/
"""
# 按顺序，如果这三种不能覆盖，基本就是乱码了
encoding_list = [
    "UTF8",          # 全部解码方式都失败时，强制使用此编码
    "GB18030",       # > gb2312 > gbk
    "BIG5-HKSCS",    # > big5
]

based_cn_word_file = [
    "/mine/other_github/common-standard-chinese-characters-table/level-1.txt",
    "/mine/other_github/common-standard-chinese-characters-table/cn_char.txt",
    "/mine/other_github/common-standard-chinese-characters-table/level-2.txt",
    "/mine/other_github/common-standard-chinese-characters-table/level-3.txt",
    "/mine/other_github/common-standard-chinese-characters-table/cn_ext.txt",
]
based_cn_word_sets = [set(open(fn).read().split("\n")) for fn in based_cn_word_file]
based_cn_word_set_all = set.union(*based_cn_word_sets)


class Worker(object):

    def __init__(self):
        self.encoding_cnt = {x: 0 for x in encoding_list}

    def try_decode(self, res, first_time):
        ext_encoding_cnt = {
            "total_cnt": 0,
            "absolute_cnt": 0,
            "bad_cnt": 0,
            "same_cnt": 0,
            "sure_cnt": 0,
            "guess_cnt": 0,
        }

        content_text = ""
        with open(self.infile, "rb") as fr:
            while True:
                line = fr.readline()
                if not line:
                    break
                else:
                    ext_encoding_cnt["total_cnt"] = ext_encoding_cnt["total_cnt"] + 1

                    # 保存每个的解码结果
                    tmp_res = {}
                    for encoding in encoding_list:
                        try:
                            tmp_res[encoding] = line.decode(encoding)
                        except Exception:
                            pass

                    # 情况1: 多个编码解析成功，所有结果都一样（通常是英文）
                    # 情况2: 只有1个编码解析成功
                    # 任意取1个结果
                    if len(set(tmp_res.values())) == 1:
                        if len(tmp_res) == 1:
                            encoding = list(tmp_res.keys())[0]
                            self.encoding_cnt[encoding] = self.encoding_cnt[encoding] + 1
                        else:
                            ext_encoding_cnt["same_cnt"] = ext_encoding_cnt["same_cnt"] + 1
                            # for encoding in tmp_res:
                            #     self.encoding_cnt[encoding] = self.encoding_cnt[encoding] + 1
                        content_text = content_text + list(tmp_res.values())[0]

                    else:

                        # 情况3: 没有任何解析结果
                        # 强制使用编码列表的第一个编码 UTF8
                        # DEBUG: 可能会出问题，例如吞噬紧邻的单、双引号
                        if not tmp_res:
                            content_text = content_text + line.decode(encoding, errors="replace")
                            ext_encoding_cnt["bad_cnt"] = ext_encoding_cnt["bad_cnt"] + 1

                        # 按之前成功次数的顺序尝试比对字库
                        # 情况4: 有多个解码成功的结果，但解析结果互不相同
                        # 按常用字的出现次数来排序，取常用字出现次数最多 + 之前成功次数最多的
                        else:

                            # 情况7: 经过第一次遍历，已经得出了成功次数最多的编码
                            # 直接使用这个编码即可（只要这个编码能解出来任意一个常用字，就算OK）
                            if not first_time:

                                # 特殊说明: 如果超出常用字范围，就算真的能解出来也看不懂，所以干脆不解了，或者用常用字替代
                                res_cnt = {}
                                for encoding in tmp_res:
                                    res_cnt[encoding] = sum((1 for x in tmp_res[encoding] if x in based_cn_word_set_all))

                                # max_cnt = max(res_cnt.values())
                                for _ in [1]:
                                    tmp_res2 = {enc: txt for (enc, txt) in tmp_res.items() if res_cnt[enc] != 0}
                                    if len(tmp_res2) == 1:
                                        encoding = list(tmp_res2.keys())[0]
                                        break
                                else:
                                    sorted_encoding = sorted(self.encoding_cnt.items(), key=lambda x: -x[1])
                                    encoding = next((enc for enc, _ in sorted_encoding if enc in tmp_res))

                                ext_encoding_cnt["sure_cnt"] = ext_encoding_cnt["sure_cnt"] + 1
                                self.encoding_cnt[encoding] = self.encoding_cnt[encoding] + 1
                                content_text = content_text + tmp_res[encoding]

                            # 第一次遍历
                            else:

                                # 判断常用汉字的出现次数：按 一级字表 > 二级字表 > 三级字表 排序，使用最后留存的编码（大概率）
                                for cn_word_set in based_cn_word_sets:
                                    res_cnt = {}
                                    for encoding in tmp_res:
                                        res_cnt[encoding] = sum((1 for x in tmp_res[encoding] if x in cn_word_set))
                                    max_cnt = max(res_cnt.values())
                                    tmp_res = {enc: txt for (enc, txt) in tmp_res.items() if res_cnt[enc] == max_cnt}

                                    # 最后留存的编码只有1个
                                    if len(tmp_res) == 1:
                                        encoding = list(tmp_res.keys())[0]
                                        self.encoding_cnt[encoding] = self.encoding_cnt[encoding] + 1
                                        ext_encoding_cnt["sure_cnt"] = ext_encoding_cnt["sure_cnt"] + 1
                                        content_text = content_text + tmp_res[encoding]
                                        break

                                # 有多个编码一直解出来一样多字数的常用字
                                else:
                                    # 情况5: 有1个编码解出来了，但常用字没有覆盖到
                                    # 情况6: 里面确实存在乱码，所有编码都解错了
                                    # 指定之前成功次数最多的编码（猜测）
                                    sorted_encoding = sorted(self.encoding_cnt.items(), key=lambda x: -x[1])
                                    encoding = next((enc for enc, _ in sorted_encoding if enc in tmp_res))
                                    ext_encoding_cnt["guess_cnt"] = ext_encoding_cnt["guess_cnt"] + 1
                                    content_text = content_text + tmp_res[encoding]

        res = self.encoding_cnt.copy()
        res.update(ext_encoding_cnt)
        self.content_text = content_text

        # # 第一次检查后，把会冲突的那些编码干掉(其实都有可能，所以忽略)
        # if first_time:
        #     for pair in conflict_list:
        #         max_cnt, max_encoding = max(((self.encoding_cnt.get(enc, 0), enc) for enc in pair))
        #         list(self.encoding_cnt.pop(enc) for enc in pair if enc != max_encoding)
        #         list(encoding_list.remove(enc) for enc in pair if enc != max_encoding)

        return res

    def decode(self, infile, outfile=None):
        self.infile = infile

        print("目标文件为: %s" % (infile))

        res_t = self.try_decode(res={}, first_time=True)
        res_f = self.try_decode(res={}, first_time=False)

        for encoding in self.encoding_cnt:
            res_f[encoding] = res_f[encoding] - res_t[encoding]

        print("第一次计数:%s" % res_t)
        print("修正计数:%s" % res_f)
        if res_t == res_f:
            print("第一次计数与修正计数 100% 完全吻合")
        else:
            diff_cnt = sum(abs(res_f[cnt_type] - res_t[cnt_type]) for cnt_type in res_f) / 2
            print("第一次计数与修正计数 %s%% 吻合" % round((1 - diff_cnt / res_f["total_cnt"]) * 100, 2))

        max_encoding_cnt = max(self.encoding_cnt.values())
        max_encoding = next(enc for enc in self.encoding_cnt if self.encoding_cnt[enc] == max_encoding_cnt)

        print("主要编码为: %s (%s%%), 全文吻合率: %s%%" % (
            max_encoding,
            round(100 * max_encoding_cnt / (sum(self.encoding_cnt.values()) or 1), 2),
            round(100 * (res_f[max_encoding] + res_f["same_cnt"]) / (res_f["total_cnt"] or 1), 2),
        ))

        if outfile:
            with open(outfile, "w") as wf:
                wf.write(self.content_text)
            print("已输出到文件:%s" % outfile)

        return self.content_text
