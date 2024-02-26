import sublime
import sublime_plugin
import json

import sys
sys.path.append('/usr/local/lib/python3.9/site-packages')


class format_odpsCommand(sublime_plugin.TextCommand):

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

        res_text = main(target_text)

        # self.view.run_command("insert", {"characters": res_text})
        self.view.replace(edit, target_region, res_text)

import q
import re
import sqlparse
import uuid
from sqlparse import sql as SQL
from sqlparse import tokens as TOKEN

"""
    这个解析框架，token倒是都拆分出来了，但是拆分的效果很差

    TODO:
        特殊语法：任何地方都可能插入 <comment>
        @aaa := SELECT
"""
"""
    tokens:
        Assignment, CTE, Command, Comment, Comparison, DDL, DML,
        Error, Generic, Keyword, Literal, Name, Newline, Number,
        Operator, Punctuation, String, Text, Token, Whitespace, Wildcard,
        Other
"""

if not "TYPE1":
    """
        添加方法
    """
    def x(self):
        info = self.inspect.getframeinfo(self.sys._getframe(1))
        return str(("Q:", info.function, info.lineno))
    import types
    q.__class__.x = types.MethodType(x, q.__class__)
    q = q.__class__()
    q.x()

else:
    """
        添加类方法
    """
    def x(cls):
        info = cls.inspect.getframeinfo(cls.sys._getframe(1))
        return str(("Q:", info.function, info.lineno))
    q.__class__.x = classmethod(x)
    q.x()


q.d = lambda: None


# ODPS KEYWORD
sqlparse.keywords.KEYWORDS_HQL.update({
    'PARTITIONED': TOKEN.Keyword,
    'LIFECYCLE': TOKEN.Keyword,
    'STRING': TOKEN.Keyword,
    'BIGINT': TOKEN.Keyword,
    'COMMENT': TOKEN.Keyword,
    'COALESCE': TOKEN.Keyword,
})
# sqlparse.keywords.KEYWORDS.update({
#     'PARTITIONED': TOKEN.Keyword,
#     'LIFECYCLE': TOKEN.Keyword,
#     'STRING': TOKEN.Keyword,
#     'BIGINT': TOKEN.Keyword,
#     'COMMENT': TOKEN.Keyword,
# })

KEYWORDS_NEW_LINE = (
    "PARTITIONED", "LIFECYCLE", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "JOIN", "GROUP BY",
    "UNION ALL", "UNION", "ORDER BY", "LIMIT"
)
KEYWORDS_DDLL = ("LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "JOIN")
KEYWORDS_KEEP_LOW = ("TRUE", "FALSE")
NOT_KEYWORDS = ("UID", "ID", "TABLE_NAME", "OWNER")

if True:
    [sqlparse.keywords.KEYWORDS.pop(x, None) for x in NOT_KEYWORDS]

if True:
    TOKEN.Token.BOF = TOKEN.Token.BOF
    TOKEN.Token.EOF = TOKEN.Token.EOF
    TOKEN.Token.Function.Start = TOKEN.Token.Function.Start
    TOKEN.Token.Parenthesis.Start = TOKEN.Token.Parenthesis.Start
    TOKEN.Token.DDL.Start = TOKEN.Token.DDL.Start
    TOKEN.Token.Where.Start = TOKEN.Token.Where.Start
    TOKEN.Token.Comparison.Start = TOKEN.Token.Comparison.Start
    TOKEN.Token.odps.Start = TOKEN.Token.odps.Start
    TOKEN.Token.Identifier.Start = TOKEN.Token.Identifier.Start
    TOKEN.Token.IdentifierList.Start = TOKEN.Token.IdentifierList.Start
    TOKEN.Token.ColumnList.Start = TOKEN.Token.ColumnList.Start
    TOKEN.Token.From.Start = TOKEN.Token.From.Start
    TOKEN.Token.Join.Start = TOKEN.Token.Join.Start

# sqlparse.keywords.is_keyword()


class Worker(object):

    def __init__(self):
        self.zbuff = ""
        self.PARENTHESIS_MAX_LEN = None
        self.LINE_TAB_CNT = 0
        self.TAB_SPACE = "    "
        self.LINE_START = True
        self.COL_NAME_START = False
        self.DEBUG = False
        self.STAT_ERROR = False
        self.stat_stack = []
        self.stat_stack_type = []
        self.global_stat = [TOKEN.Token.BOF]
        self.LAST_IS_COMMENT = False
        self.KEEP_ALL = False
        self.IS_IN_WHERE = False
        self.IS_WHERE_FIRST = False
        self.IS_WHERE_PAR_FIRST = False
        self.LAST_IS_NR = False
        self.LAST_IS_BETWEEN = False

    def is_token_whitespace(self, token):
        return type(token) is SQL.Token and token.ttype is TOKEN.Text.Whitespace

    def is_token_newline(self, token):
        return type(token) is SQL.Token and token.ttype is TOKEN.Text.Whitespace.Newline

    def closest_is_ddl(self, stat_stack):
        for i in range(len(self.stat_stack) -1, 0, -1):
            if self.stat_stack[i - 1].ttype in (TOKEN.Keyword.DML, TOKEN.Keyword.DDL, TOKEN.Keyword.CTE):
                return True
            elif self.stat_stack[i - 1].ttype in (TOKEN.Text.Whitespace, TOKEN.Keyword, TOKEN.Text.Whitespace.Newline):
                continue
            else:
                return False

    def get_new_line(self, prefix=0):
        return "\n" + self.TAB_SPACE * (self.LINE_TAB_CNT + prefix)

    def prefix_space(self):
        if self.COL_NAME_START:
            self.COL_NAME_START = False
            return ""
        else:
            return " "

    def trim_rspace(self, text):

        while text and text[-1] in (" ", ):
            text = text[:-1]

        return text

    def trim_lspace(self, text):

        while text and text[0] in (" ", ):
            text = text[1:]

        return text

    # def set_token_ttype(self, token, ttype):
    #     # next_token.tokens[27] = SQL.Token(TOKEN.Token.Name, token.value)
    #     grouping.group_identifier(aa)
    #     SQL.Identifier([aa])
    #     # set_token_as_name()
    #     token.ttype = ttype

    def convert_token_to_identifier(self, token):
        token_n = SQL.Token(TOKEN.Token.Name, token.value)
        return SQL.Identifier([token_n])

    def makeup_col_list(self, tokens):
        has_parenthesis = False
        if tokens[0].value == "(" and tokens[-1].value == ")":
            has_parenthesis = True

        # 拆开 IdentifierList
        for i in range(len(tokens) - 1, -1, -1):
            if type(tokens[i]) in (SQL.IdentifierList, ):
                tokens[i: i+1] = tokens[i].tokens

        # q.d()
        # 使用 NOT_KEYWORDS 后，不会发生，无须处理
        for i, token in enumerate(tokens):
            if type(tokens[i]) not in (SQL.Token, ):
                continue
            if tokens[i].ttype in (TOKEN.Text.Whitespace, TOKEN.Text.Whitespace.Newline):
                continue
            if tokens[i].value in NOT_KEYWORDS:
                print("NOT_KEYWORDS:", type(tokens[i]), i, tokens[i].value)
                tokens[i] = self.convert_token_to_identifier(tokens[i])

        col_names = [y for x in tokens if type(x) == SQL.Identifier for y in x.tokens if y.ttype == TOKEN.Token.Name]
        if col_names:
            return max([len(x.value) for x in col_names])
        else:
            return None

        # next_token.tokens[27] = self.convert_token_to_identifier(next_token.tokens[27])

    def make_punctuation_right(self, tokens, iloop):

        istop = 0
        for i, token in enumerate(tokens):
            if i <= iloop:
                continue
            if type(token) == SQL.Token and token.ttype == TOKEN.Token.Keyword:
                if token.value == "FROM":
                    istop = i
                    break
        else:
            print("make_punctuation_right: nothing to do")
            return

        print("make_punctuation_right:", iloop, istop)
        # q.d()
        for i in range(istop - 1, iloop, -1):
            this_token = tokens[i]
            if type(this_token) == SQL.Identifier:
                for j in range(i - 1, iloop - 1, -1):
                    pre_token = tokens[j]
                    if type(pre_token) == SQL.Function:
                        break
                    if type(pre_token) == SQL.Token and pre_token.ttype == TOKEN.Token.Punctuation and pre_token.value == ",":
                        # 如果前1个token是[,]，则跳过，否则将最近的 [,] 移动
                        if i - 1 == j:
                            pass
                        else:
                            tokens[j: i] = tokens[j + 1: i] + tokens[j:j + 1]
                        break
                else:
                    pass

        # q.d()
        col_names = [y for x in tokens[iloop: istop] if type(x) == SQL.Identifier for y in x.tokens if y.ttype == TOKEN.Token.Name]
        if col_names:
            self.PARENTHESIS_MAX_LEN = max([len(x.value) for x in col_names])
        else:
            self.PARENTHESIS_MAX_LEN = None

        # self.PARENTHESIS_MAX_LEN = 1
        # tokens[iloop: istop]

    def get_name_from_identifier(self, token):
        tokens = SQL.Identifier([x for x in token.tokens
            if not (type(x) == SQL.Token and x.ttype in (TOKEN.Token.Text.Whitespace, TOKEN.Text.Whitespace.Newline))
            and not (type(x) == SQL.Comment)
        ])
        return tokens.value

    def split_identifier(self, token):
        tokens = [x for x in token.tokens]
        goon = True
        comment = ""
        # q.d()
        while goon:
            goon = False
            if (type(tokens[-1]) == SQL.Token and tokens[-1].ttype in (TOKEN.Token.Text.Whitespace, TOKEN.Text.Whitespace.Newline)):
                if tokens[-1].ttype in TOKEN.Text.Whitespace.Newline:
                    if comment:
                        self.LAST_IS_NR = True
                tokens.pop()
                goon = True
            if (type(tokens[-1]) == SQL.Comment):
                comment = tokens[-1].value.rstrip()
                tokens.pop()
                goon = True

        # for token in token.tokens:
        #     tokens.append(" ")
        # tokens = SQL.Identifier([x for x in token.tokens
        #     if not (type(x) == SQL.Token and x.ttype in (TOKEN.Token.Text.Whitespace, TOKEN.Text.Whitespace.Newline))
        #     and not (type(x) == SQL.Comment)
        # ])
        return SQL.Identifier(tokens).value, comment

    def keyword_to_upper(self, tokens):
        for token in tokens:
            token_type = type(token)
            if token_type is SQL.Token:
                if token.ttype in (TOKEN.Keyword, TOKEN.Token.Keyword.DML, TOKEN.Token.Keyword.DDL, TOKEN.Token.Keyword.CTE, TOKEN.Token.Operator.Comparison):
                    token.value = token.value.upper()
                    # print(token_type, token.value)
                # else:
                    # print(token_type, token.value)

            if hasattr(token, 'tokens'):
                self.keyword_to_upper(token.tokens)

            token.value = str(token)

    # def token_is_complix(self, tokens):
    #     for token in tokens:
    #         if

    def work_in_tokens(self, tokens):

        # 拆开 IdentifierList
        for i in range(len(tokens) - 1, -1, -1):
            if type(tokens[i]) in (SQL.IdentifierList, ):
                tokens[i: i+1] = tokens[i].tokens

        # todo_tokens = [x for x in tokens if not (type(x) is SQL.Token and x.ttype in (TOKEN.Whitespace, TOKEN.Newline))]
        todo_tokens = tokens

        for iloop, next_token in enumerate(todo_tokens):

            self.LAST_IS_NR = False

            if not self.KEEP_ALL:
                if type(next_token) is SQL.Token and next_token.ttype in (TOKEN.Whitespace, TOKEN.Newline):
                    if next_token.ttype in (TOKEN.Newline, ):
                        self.LAST_IS_NR = True
                    continue
                # else:
                #     self.IS_WHERE_PAR_FIRST = False

            token_type = type(next_token)
            if token_type is SQL.Token:
                # # 跳过所有空格和换行，自行处理
                # if next_token.ttype in (TOKEN.Whitespace, TOKEN.Newline):
                #     continue
                if type(next_token) is SQL.Token and next_token.ttype in (TOKEN.Whitespace, TOKEN.Newline):
                    pass
                else:
                    self.IS_WHERE_PAR_FIRST = False
                    print("%s %s [ %s ]" % (type(next_token), next_token.ttype, next_token.value.replace("\n", "\\n")), q.x())
            else:
                print("%s [ %s ]" % (type(next_token), next_token.value.replace("\n", "\\n")), q.x())

            # if next_token.value == "user_name":
            #     q.d()

            # if next_token.value == "where":
            #     q.d()
            # if self.DEBUG:
            #     q.d()

            if self.STAT_ERROR:
                self.zbuff = self.zbuff + next_token.value
                continue

            if token_type is SQL.Comment:

                if self.LINE_START:
                    self.zbuff = self.zbuff + self.TAB_SPACE * self.LINE_TAB_CNT + self.trim_rspace(next_token.value)
                else:
                    # next_token.tokens
                    self.zbuff = self.zbuff + "  " + next_token.value.strip()

                self.LINE_START = False
                self.LAST_IS_COMMENT = 2

            elif token_type is SQL.Token:

                # if self.LAST_IS_COMMENT:
                #     self.zbuff = self.zbuff + self.get_new_line()
                #     self.LAST_IS_COMMENT = False

                # 跳过所有空格和换行，自行处理
                if next_token.ttype in (TOKEN.Whitespace, TOKEN.Newline):
                    continue

                # 遇到标点符号，则前后设为空格
                if next_token.ttype in (TOKEN.Punctuation, TOKEN.Comparison):

                    # q.d()
                    # self.LINE_START
                    # self.LINE_START
                    # if next_token.value == ")":
                    #     print(next_token)
                    #     q.d()

                    if self.global_stat[-1] == TOKEN.Token.Parenthesis.Start:
                        if self.IS_IN_WHERE:
                            if next_token.value == "(":
                                # q.d()
                                # self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                                # print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                                self.zbuff = self.zbuff + next_token.value
                                self.IS_WHERE_PAR_FIRST = True
                            elif next_token.value == ")":
                                # q.d()
                                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                                self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                            else:
                                self.zbuff = self.zbuff + " " + next_token.value
                        else:
                            if next_token.value == ")":
                                # q.d()
                                # self.global_stat.pop()
                                # print("📒 8:", self.global_stat, q.x())
                                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                                self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                            else:
                                self.zbuff = self.zbuff + next_token.value
                    # else:
                        # if self.global_stat[-1] == TOKEN.Token.IdentifierList.Start:
                    elif self.global_stat[-1] in (TOKEN.Token.ColumnList.Start, TOKEN.Token.From.Start):

                        if next_token.value == ")":

                            if self.global_stat[-1] in (TOKEN.Token.From.Start, ):
                                # if next_token.value in KEYWORDS_DDLL:
                                # q.d()
                                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                                self.global_stat.pop()
                                print("📒 8:", self.global_stat, q.x())
                                print("\n\n\n")

                            # self.global_stat.pop()
                            # print("📒 8:", self.global_stat, q.x())
                            self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                            print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                            self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        elif next_token.value == ",":
                            self.COL_NAME_START = True
                            print("Got COL_NAME_START")
                            self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        elif next_token.value == "(":
                            self.zbuff = self.zbuff + next_token.value
                        elif next_token.value == ";":
                            self.zbuff = self.zbuff + "\n" + next_token.value
                        else:
                            self.zbuff = self.zbuff + " " + next_token.value

                    else:
                        # q.d()
                        if next_token.value == ";":
                            if self.global_stat[-1] == TOKEN.Token.odps.Start:
                                self.zbuff = self.zbuff + next_token.value
                            else:
                                self.zbuff = self.zbuff + "\n" + next_token.value
                        elif next_token.value == ".":
                            self.zbuff = self.zbuff + next_token.value
                        else:
                            self.zbuff = self.zbuff + self.prefix_space() + next_token.value
                            # self.zbuff = self.zbuff + self.prefix_space() + next_token.value + " "

                # 关键字
                elif next_token.ttype in (TOKEN.Keyword, ):

                    # if self.LAST_IS_COMMENT:
                    #     self.zbuff = self.zbuff + "\n"

                    # if next_token.value in ("JOIN", ):
                    #     print("get join")
                    #     q.d()

                    # q.d()

                    if self.global_stat[-1] == TOKEN.Token.BOF and next_token.value in ("SET", ):
                        self.zbuff = self.zbuff + next_token.value
                        self.global_stat.append(TOKEN.Token.odps.Start)
                        print("📒 9:", self.global_stat, q.x())
                    elif self.global_stat[-1] == TOKEN.Token.Where.Start and next_token.value in ("WHERE", ):
                        self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        # self.zbuff = self.zbuff + self.get_new_line(-1) + next_token.value
                        self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                        print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                        self.LINE_START = True

                    elif self.global_stat[-1] == TOKEN.Token.Where.Start and next_token.value in ("BETWEEN", ):
                        self.zbuff = self.zbuff + " " + next_token.value
                        self.LAST_IS_BETWEEN = True

                    elif self.global_stat[-1] == TOKEN.Token.ColumnList.Start and next_token.value in ("FROM", ):
                        self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                        print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                        self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        # self.zbuff = self.zbuff + self.get_new_line(-1) + next_token.value
                        # q.d()
                        self.global_stat.pop()
                        print("📒 8:", self.global_stat, q.x())
                        self.LINE_START = True
                        self.global_stat.append(TOKEN.Token.From.Start)
                        print("📒 9:", self.global_stat, q.x())
                        self.PARENTHESIS_MAX_LEN = None
                        self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                        print("📝 change linexx", self.LINE_TAB_CNT, q.x())

                    elif self.global_stat[-1] == TOKEN.Token.DDL.Start and next_token.value in KEYWORDS_NEW_LINE:
                        print("GET KEYWORDS_NEW_LINE 1:", next_token)
                        if "JOIN" in next_token.value:
                            self.global_stat.append(TOKEN.Token.Join.Start)
                            print("📒 9:", self.global_stat, q.x())

                        self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                    elif self.LAST_IS_COMMENT:
                        self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                    else:
                        if self.LAST_IS_BETWEEN and next_token.value == "AND":
                            self.zbuff = self.zbuff + self.prefix_space() + next_token.value
                        elif next_token.value in ("AND", "OR") and self.global_stat[-1] not in (TOKEN.Token.Join.Start, ):
                            self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        elif next_token.value in KEYWORDS_KEEP_LOW:
                            self.zbuff = self.zbuff + self.prefix_space() + next_token.value.lower()
                        elif next_token.value in KEYWORDS_NEW_LINE:

                            print("GET KEYWORDS_NEW_LINE 2:", next_token)
                            if self.global_stat[-1] in (TOKEN.Token.From.Start, TOKEN.Token.DDL.Start):
                                # if next_token.value in KEYWORDS_DDLL:
                                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                                self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                                # q.d()
                                self.global_stat.pop()
                                print("📒 8:", self.global_stat, q.x())
                                self.global_stat.append(TOKEN.Token.Join.Start)
                                print("📒 9:", self.global_stat, q.x())

                                # self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                            else:
                                self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                            #     self.global_stat.pop()
                            # print("📒 8:", self.global_stat, q.x())
                            #     self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                            # self.zbuff = self.zbuff + self.get_new_line(-1) + next_token.value
                        else:
                            self.zbuff = self.zbuff + self.prefix_space() + next_token.value

                # DDL / DML / CTE
                elif next_token.ttype in (TOKEN.Keyword.DML, TOKEN.Keyword.DDL, TOKEN.Keyword.CTE):

                    if next_token.value == "SELECT":
                        # self.PARENTHESIS_MAX_LEN = self.makeup_col_list(next_token.tokens)
                        # # self.global_stat.append(TOKEN.Token.Parenthesis.Start)
                        # print("📒 9:", self.global_stat, q.x())
                        print("GET SELECT")
                        # self.COL_NAME_START = True
                        if self.LINE_TAB_CNT > 1 and self.global_stat[-1] in (TOKEN.Token.Parenthesis.Start, ):
                            if self.global_stat[-2] in (TOKEN.Token.From.Start, ):
                                # q.d()
                                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                            elif self.global_stat[-2] in (TOKEN.Token.Join.Start, ):
                                # q.d()
                                pass
                        else:
                            pass

                        self.global_stat.append(TOKEN.Token.ColumnList.Start)
                        print("📒 9:", self.global_stat, q.x())
                        if not self.zbuff:
                            self.zbuff = next_token.value
                        else:
                            self.zbuff = self.zbuff + self.get_new_line() + next_token.value
                        self.make_punctuation_right(todo_tokens, iloop)
                        self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                        print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                        self.LINE_START = True
                        # self.DEBUG = True
                        # q.d()

                    elif self.global_stat[-1] == TOKEN.Token.DDL.Start:
                        # q.d()
                        # self.zbuff = self.zbuff + " " + next_token.value
                        self.zbuff = self.zbuff + self.get_new_line() + next_token.value

                    elif not self.zbuff:
                        self.global_stat.append(TOKEN.Token.DDL.Start)
                        print("📒 9:", self.global_stat, q.x())
                        self.zbuff = next_token.value

                    else:
                        self.global_stat.append(TOKEN.Token.DDL.Start)
                        print("📒 9:", self.global_stat, q.x())
                        self.zbuff = self.zbuff + next_token.value
                        q.d()

                # 解析错误，一般是 ODPS 自定义语法，例如 ${ds} （已处理）
                elif next_token.ttype in (TOKEN.Error, ):
                    self.STAT_ERROR = True
                    self.zbuff = self.zbuff + " " + next_token.value

                # 一般是字段名 / 表名 / 别名
                elif next_token.ttype in (TOKEN.Name, ):
                    self.zbuff = self.zbuff + next_token.value

                elif next_token.ttype in (TOKEN.Token.Literal.String.Single, TOKEN.Token.Literal.Number.Integer):
                    self.zbuff = self.zbuff + " " + next_token.value

                else:
                    # q.d()
                    # q.d()
                    self.zbuff = self.zbuff + " " + next_token.value

            elif token_type in (SQL.Function, ):
                print("IS Function..")
                # 建表语句/DDL/DML 语句
                if self.closest_is_ddl(self.stat_stack):
                    self.global_stat.append(TOKEN.Token.Function.Start)
                    print("📒 9:", self.global_stat, q.x())
                    self.work_in_tokens(next_token.tokens)
                    self.global_stat.pop()
                    print("📒 8:", self.global_stat, q.x())
                    self.LINE_START = False
                elif self.global_stat[-1] == TOKEN.Token.ColumnList.Start:
                    print("SKIP with function..", next_token.value)
                    self.zbuff = self.zbuff + next_token.value.rstrip() + " "
                # 框架解析错误
                elif sqlparse.keywords.is_keyword(next_token.tokens[0].value):
                    # q.d()
                    print("IS a KEYWORDS, SKIP function:", next_token.tokens[0])
                    next_token.tokens[0] = SQL.Token(TOKEN.Token.Keyword, next_token.tokens[0].value.upper())
                    self.work_in_tokens(next_token.tokens)
                    continue
                else:
                    print("Do nothing in Function")
                    # self.global_stat.append(TOKEN.Token.Function.Start)
                    # q.d()

            elif token_type in (SQL.Parenthesis, ):
                print("IN Parenthesis..")
                # q.d()

                # 如果是比如建表语句，算出字段名的最大长度
                if self.global_stat[-1] == TOKEN.Token.Function.Start and self.global_stat[-2] == TOKEN.Token.DDL.Start or self.global_stat[-1] == TOKEN.Token.DDL.Start:
                    self.PARENTHESIS_MAX_LEN = self.makeup_col_list(next_token.tokens)
                    # self.global_stat.append(TOKEN.Token.Parenthesis.Start)
                    # print("📒 9:", self.global_stat, q.x())
                    self.global_stat.append(TOKEN.Token.ColumnList.Start)
                    print("📒 9:", self.global_stat, q.x())
                    # next_token.tokens[27] = self.convert_token_to_identifier(next_token.tokens[27])
                    # q.d()
                    # all_identifier = [x for x in next_token.tokens if type(x) == SQL.Identifier]
                    # all_identifier = all_identifier + [y for x in next_token.tokens if type(x) == SQL.IdentifierList for y in x if type(y) == SQL.Identifier]
                    # all_identifier_name = [y for x in all_identifier for y in x.tokens if y.ttype == TOKEN.Token.Name]
                    # self.PARENTHESIS_MAX_LEN = max([len(x.value) for x in all_identifier_name])
                    # q.d()

                    # next_token.tokens[27] = SQL.Token(TOKEN.Token.Name, next_token.tokens[27].value)

                    # max_out_len = max([len(x.value) for x in next_token.tokens if type(x) == SQL.Identifier])
                    # max_in_len = max([len(x[-1].value) for x in next_token.tokens if type(x) == SQL.IdentifierList])
                    # self.PARENTHESIS_MAX_LEN = max(max_out_len, max_in_len)
                elif self.global_stat[-1] == TOKEN.Token.Join.Start:
                    self.global_stat.append(TOKEN.Token.Parenthesis.Start)
                    print("📒 9:", self.global_stat, q.x())
                else:
                    self.global_stat.append(TOKEN.Token.Parenthesis.Start)
                    print("📒 9:", self.global_stat, q.x())

                self.zbuff = self.zbuff + " "
                self.LINE_TAB_CNT = self.LINE_TAB_CNT + 1
                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                self.LINE_START = True
                self.work_in_tokens(next_token.tokens)

                print("OUT Parenthesis..")
                if self.global_stat[-2] in (TOKEN.Token.From.Start, ):
                    self.global_stat.pop()
                    print("📒 8:", self.global_stat, q.x())

                self.global_stat.pop()
                print("📒 8:", self.global_stat, q.x())

            elif token_type in (SQL.IdentifierList, ):
                print("IS IdentifierList..")
                # self.global_stat.append(TOKEN.Token.IdentifierList.Start)
                # print("📒 9:", self.global_stat, q.x())
                self.work_in_tokens(next_token.tokens)
                # self.global_stat.pop()
                # print("📒 8:", self.global_stat, q.x())

            # sqlparse 库解析这个 token 有问题
            elif token_type is SQL.Identifier:

                if next((x for x in next_token.tokens if hasattr(x, "tokens")), None):
                    if self.global_stat[-1] in (TOKEN.Token.ColumnList.Start, ):
                        if self.LINE_START:
                            self.zbuff = self.zbuff + self.get_new_line() + self.prefix_space() + next_token.value.rstrip()
                        else:
                            self.zbuff = self.zbuff + self.prefix_space() + next_token.value.rstrip()
                    else:
                        # q.d()
                        self.zbuff = self.zbuff + " "
                        print("work work...")
                        self.work_in_tokens(next_token.tokens)
                else:
                    # 如果最后的一个token是 Name，如 xp_cp.tmp_ay_tb1，忽略
                    if type(next_token.tokens[-1]) == SQL.Token and next_token.tokens[-1].ttype == TOKEN.Name or self.IS_IN_WHERE:
                        # q.d()
                        key_name, comment = next_token.value.rstrip(), ""
                    # elif self.IS_IN_WHERE:
                    #     key_name, comment = self.split_identifier(next_token)
                    # 如果包含了复杂类型
                    else:
                        key_name, comment = self.split_identifier(next_token)
                        # self.LAST_IS_NR = True

                    if self.LINE_START and self.global_stat[-1] in (TOKEN.Token.ColumnList.Start, ):

                        if not self.PARENTHESIS_MAX_LEN:
                            self.zbuff = self.zbuff + self.get_new_line() + self.prefix_space() + key_name
                        elif not comment:
                            self.zbuff = self.zbuff + self.get_new_line() + self.prefix_space() + key_name
                        # elif self.LAST_IS_NR:
                        #     self.zbuff = self.zbuff + self.get_new_line() + self.prefix_space() + key_name + self.get_new_line() + comment
                        else:
                            self.zbuff = self.zbuff + self.get_new_line() + self.prefix_space() + key_name + " " * (self.PARENTHESIS_MAX_LEN - len(key_name))

                    elif self.LINE_START and self.global_stat[-1] in (TOKEN.Token.From.Start, TOKEN.Token.Where.Start) or self.IS_IN_WHERE:

                        if not self.PARENTHESIS_MAX_LEN:
                            self.zbuff = self.zbuff + self.get_new_line() + key_name
                        elif not comment:
                            self.zbuff = self.zbuff + self.prefix_space() + key_name
                        # elif self.LAST_IS_NR:
                        #     q.d()
                        else:
                            self.zbuff = self.zbuff + self.get_new_line() + key_name + " " * (self.PARENTHESIS_MAX_LEN - len(key_name))

                    else:

                        if key_name.startswith("@"):
                            self.zbuff = self.zbuff + key_name
                        elif not self.PARENTHESIS_MAX_LEN:
                            self.zbuff = self.zbuff + self.prefix_space() + key_name
                        elif not comment:
                            self.zbuff = self.zbuff + self.prefix_space() + key_name
                        # elif self.LAST_IS_NR:
                        #     q.d()
                        else:
                            self.zbuff = self.zbuff + self.prefix_space() + key_name + " " * (self.PARENTHESIS_MAX_LEN - len(key_name))

                    # ## from <Identifier>
                    # ## where <Identifier>
                    # if self.global_stat[-1] in (TOKEN.Token.From.Start, ):
                    #     # self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                    #     # print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                    #     self.global_stat.pop()
                    # print("📒 8:", self.global_stat, q.x())
                    # else:
                    #     pass

                    if comment:
                        self.LAST_IS_COMMENT = 2
                        if self.LAST_IS_NR:
                            self.zbuff = self.zbuff + self.get_new_line() + comment
                        else:
                            self.zbuff = self.zbuff + " " + comment

                    # if self.global_stat[-1] in (TOKEN.Token.From.Start, ):
                    #     self.global_stat.pop()
                    # print("📒 8:", self.global_stat, q.x())
                    #     self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1

                self.LINE_START = False

            elif token_type in (SQL.Where, ):
                print("IN Where..")
                self.IS_IN_WHERE = True
                self.IS_WHERE_FIRST = True
                if self.global_stat[-1] in (TOKEN.Token.From.Start, ):
                    self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                    print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                    self.global_stat.pop()
                    print("📒 8:", self.global_stat, q.x())
                if self.global_stat[-1] in (TOKEN.Token.Join.Start, ):
                    self.global_stat.pop()
                    print("📒 8:", self.global_stat, q.x())
                self.global_stat.append(TOKEN.Token.Where.Start)
                print("📒 9:", self.global_stat, q.x())
                self.KEEP_ALL = True
                self.work_in_tokens(next_token.tokens)
                print("OUT Where..")
                # q.d()
                self.LINE_TAB_CNT = self.LINE_TAB_CNT - 1
                print("📝 change linexx", self.LINE_TAB_CNT, q.x())
                self.global_stat.pop()
                print("📒 8:", self.global_stat, q.x())
                self.KEEP_ALL = False
                self.PARENTHESIS_MAX_LEN = None
                self.IS_IN_WHERE = False

            # 框架解析出来的为什么连注释都在表达式里面。。。
            elif token_type in (SQL.Comparison, ):
                print("IS Comparison..")
                # self.global_stat.append(TOKEN.Token.Comparison.Start)
                # print("📒 9:", self.global_stat, q.x())
                # self.DEBUG = True
                # 在 where 的 括号里

                # print(next_token.value)
                # q.d()

                # comp_text = self.pretty_comparison_text(next_token)
                if type(next_token.tokens[-1]) == SQL.Comment:
                    comp_text = " ".join([token.value.strip() for token in next_token.tokens[:-1] if token.value.strip() ])
                    self.LAST_IS_COMMENT = 2
                    print("cccccccccc:", comp_text)
                    for tk in next_token.tokens[::-1][1:]:
                        if type(tk) is SQL.Token and tk.ttype in (TOKEN.Whitespace, TOKEN.Newline):
                            if tk.ttype in (TOKEN.Newline, ):
                                self.LAST_IS_NR = True
                                break
                        else:
                            self.LAST_IS_NR = False
                            break
                    else:
                        self.LAST_IS_NR = False
                    comment = next_token.tokens[-1].value.strip()
                    # q.d()
                else:
                    comp_text = " ".join([token.value.strip() for token in next_token.tokens if token.value.strip() ])
                    comment = ""

                # q.d()

                if self.IS_IN_WHERE:
                    if self.IS_WHERE_FIRST:
                        self.zbuff = self.zbuff + self.get_new_line() + comp_text
                        self.IS_WHERE_FIRST = False
                    elif self.IS_WHERE_PAR_FIRST:
                        self.zbuff = self.zbuff + self.get_new_line() + comp_text
                        self.IS_WHERE_PAR_FIRST = False
                    else:
                         self.zbuff = self.zbuff + " " + comp_text

                    if self.LAST_IS_NR:
                        self.zbuff = self.zbuff + self.get_new_line() + comment
                    elif comment:
                        self.zbuff = self.zbuff + " " + comment
                    else:
                        pass

                else:
                    self.work_in_tokens(next_token.tokens)
                # self.global_stat.pop()
                # print("📒 8:", self.global_stat, q.x())

            else:
                self.zbuff = self.zbuff + " " + next_token.value
                self.LINE_START = False

            if self.LAST_IS_COMMENT == 2:
                self.LAST_IS_COMMENT = True
            else:
                self.LAST_IS_COMMENT = False

            self.stat_stack.append(next_token)
            self.stat_stack_type.append(token_type)

    # def pretty_comparison_text(self, token):
    #     comp_text = " ".join([token.value for token in token.tokens])

    #     return comp_text


class lateReplace():

    def __init__(self):
        self.default_escape = "az_" + uuid.uuid4().hex
        self.re_cache = []

    def prepare(self, line, rstring):
        return re.sub(rstring, self.re_escape, line)

    def refill(self, line):
        self.re_cache = self.re_cache[::-1]
        return re.sub("(%s)" % self.default_escape, self.re_unescape, line)

    def re_escape(self, match):
        self.re_cache.append(match.group(0))
        return self.default_escape

    def re_unescape(self, match):
        return self.re_cache.pop()

q.d = lambda: None
print = lambda *a, **b: None

def main(sql_text):


    lr = lateReplace()
    pre_work_text = lr.prepare(sql_text, r"\$\{.*?\}")
    done_buff = []

    # parsed = sqlparse.parse(pre_work_text)[0]    #
    for parsed in sqlparse.parse(pre_work_text):

        wk = Worker()

        wk.keyword_to_upper(parsed.tokens)
        wk.work_in_tokens(parsed.tokens)
        done_buff.append(wk.zbuff)

    done_text = lr.refill("\n\n".join(done_buff))

    return done_text
