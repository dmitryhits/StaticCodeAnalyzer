# write your code here
from pathlib import Path
import argparse
import re
import ast

class CodeAnalyzer:
    def __init__(self, file):
        self.file = file
        self.file_string = ""
        # print(file.name)
        self.max_line_length = 79
        self.max_blank_lines = 2
        self.blank_line_count = 0
        self.errors = {}

    def process_file(self):
        for i, line in enumerate(self.file):
            self.file_string += line
            self.check_line_length(i, line)
            self.check_indentation(i, line)
            self.consecutive_blank_lines(i, line)
            self.inline_comment_spaces(i, line)
            line = self.remove_string(line)
            line, comment = self.remove_comments(line)
            self.semicolon(i, line)
            self.find_todo(i, comment)
            self.find_class(i, line)
            self.find_function(i, line)
        self.check_function_arguments()


    def print_errors(self):
        for line in self.errors:
            for error, info in sorted(set(self.errors[line])):
                if error == 'S001':
                    message = 'Too long'
                elif error == 'S002':
                    message = 'Indentation is not a multiple of four'
                elif error == 'S003':
                    message = 'Unnecessary semicolon after a statement'
                elif error == 'S004':
                    message = 'Less than two spaces before inline comments'
                elif error == 'S005':
                    message = 'TODO found'
                elif error == 'S006':
                    message = 'More than two blank lines preceding a code line'
                elif error == 'S007':
                    message = 'Too many spaces after construction_name (def or class)'
                elif error == 'S008':
                    message = f'Class name {info} should be written in CamelCase'
                elif error == 'S009':
                    message = f'Function name {info} should be written in snake_case'
                elif error == 'S010':
                    message = f'Argument name {info} should be written in snake_case'
                elif error == 'S011':
                    message = f'Variable {info} should be written in snake_case'
                elif error == 'S012':
                    message = f'The default argument value is mutable'
                print(f'{self.file.name}: Line {line + 1}: {error} {message}')

    def check_line_length(self, i, line):
        if len(line) > self.max_line_length:
            self.errors.setdefault(i, []).append(('S001', ''))
            # print(f'Line {i + 1}: S001 Too long')

    def check_indentation(self, i, line):
        space_count = 0
        for c in line:
            if c.isspace():
                space_count += 1
            else:
                break
        if space_count:
            if space_count < len(line) and space_count % 4:
                self.errors.setdefault(i, []).append(('S002', ''))
                # print(f'Line {i + 1}: S002 Indentation is not a multiple of four')

    def remove_string(self, line):
        comments = ['"""', "'''", '"', "'"]
        for sign in comments:
            if line.count(sign) == 2:
                front = line.find(sign)
                end = line.rfind(sign)
                line = line[:front] + line[end:]
        return line

    def inline_comment_spaces(self, i, line):
        if '#' in line:
            comment_start = line.find('#')
            if comment_start > 0 and line[comment_start - 2: comment_start] != "  ":
                self.errors.setdefault(i, []).append(('S004', ''))
                # print(f"Line {i + 1}: S004 Less than two spaces before inline comments")

    def remove_comments(self, line):
        comment = ''
        if '#' in line:
            comment_start = line.find('#')
            comment = line[comment_start:]
            line = line[:comment_start]
        return line, comment

    def consecutive_blank_lines(self, i, line):
        if line and not line.isspace():
            if self.blank_line_count > self.max_blank_lines:
                # print(f'Line {i + 1}: S006 More than two blank lines preceding a code line '
                #       f'(applies to the first non-empty line).')
                self.errors.setdefault(i, []).append(('S006', ''))
            self.blank_line_count = 0
        else:
            self.blank_line_count += 1

    def semicolon(self, i, line):
        if ';' in line:
            self.errors.setdefault(i, []).append(('S003', ''))
            # print(f'Line {i + 1}: S003  Unnecessary semicolon after a statement '
            #       f'(note that semicolons are acceptable in comments)')

    def find_todo(self, i, comment):
        comment = comment.lower()
        # print(comment)
        if 'todo' in comment:
            self.errors.setdefault(i, []).append(('S005', ''))
            # print(f'Line {i + 1}: S005 TODO found')

    def find_class(self, i, line):
        # pattern = r'''
        # ( *)              # indentation spaces [0]
        # class
        # ( +)              # spaces before class name [1]
        # (\w+)             # class name [2]
        # (\([\w ,]\))?     # parent class names [3]
        # :
        # '''
        pattern = r'( *)class( +)(\w+)(\([\w ,]\))?:'
        p = re.compile(pattern)
        m = p.match(line)
        class_name = ''
        spaces = ''
        if m:
            class_name = m.groups()[2]
            spaces = m.groups()[1]
            # print(f'class name is {class_name}')
            if class_name.lower() == class_name:
                # print('wrong class')
                self.errors.setdefault(i, []).append(('S008', class_name))
            if len(spaces) > 1:
                self.errors.setdefault(i, []).append(('S007', ''))

    def find_function(self, i, line):
        # pattern = r'''
        #         ( *)          # indentation spaces [0]
        #         def
        #         ( +)          # spaces before function name [1]
        #         (_{0,2})      # optional underscores [2]
        #         (\w+)         # function name [3]
        #         (_{0,2})      # optional underscores [4]
        #         \([\w ,:]*\)  # arguments
        #         :
        #         '''
        pattern = r'( *)def( +)(_{0,2})(\w+)(_{0,2})\([\w ,:]*\):'
        p = re.compile(pattern)
        m = p.match(line)
        function_name = ''
        spaces = ''
        if m:
            function_name = m.groups()[3]
            spaces = m.groups()[1]
            if function_name.lower() != function_name:
                self.errors.setdefault(i, []).append(('S009', function_name))
            if len(spaces) > 1:
                self.errors.setdefault(i, []).append(('S007', ''))

    def check_function_arguments(self):
        # print(self.file_string)
        tree = ast.parse(self.file_string)
        # print(ast.dump(tree))
        ast_analyzer = AstAnalyzer()
        ast_analyzer.visit(tree)
        # print(f'visited the tree: {ast_analyzer.function_args}')
        for f_name, f_args in ast_analyzer.function_args.items():
            # print('Looping')
            i_line = ast_analyzer.function_lineno[f_name]
            for arg in f_args:
                if not arg.islower():
                    self.errors.setdefault(i_line - 1, []).append(('S010', arg))
        for f_name, f_defaults in ast_analyzer.defaults.items():
            i_line = ast_analyzer.function_lineno[f_name]
            for default in f_defaults:
                if isinstance(default, list) or isinstance(default, dict):
                    self.errors.setdefault(i_line - 1, []).append(('S012', ''))
        for f_name, f_vars in ast_analyzer.assigned_variables.items():
            # if self.file.name == 'test/this_stage/test_3.py':
            #     print(f"Name: {f_name}, Vars: {f_vars}")
            for i_line, line_vars in f_vars.items():
                for var in line_vars:
                    if not var.islower():
                        self.errors.setdefault(i_line - 1, []).append(('S011', var))


class AssignAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.assigned_variables = {}

    def visit_Assign(self, node):
        # self.assigned_variables[node.lineno] = [el.id for el in node.targets]
        self.assigned_variables[node.lineno] = [el.id if isinstance(el, ast.Name) else el.value.id + '.' + el.attr
                                                for el in node.targets]
        #         pprint(self.assigned_variables)
        self.generic_visit(node)


class AstAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.function_args = {}
        self.function_lineno = {}
        self.assigned_variables = {}
        self.defaults = {}
        self.assign_visitor = AssignAnalyzer()

    def visit_FunctionDef(self, node):
        # print("Visiting")
        function_name = node.name
        # print(function_name)
        self.function_lineno[function_name] = node.lineno
        self.function_args[function_name] = [item.arg for item in node.args.args]
        self.defaults[function_name] = [item.value if isinstance(item, ast.Constant) else item.elts
                                        for item in node.args.defaults]
        # print(self.function_lineno)
        # print(self.function_args)
        self.assign_visitor.visit(node)
        self.assigned_variables[function_name] = self.assign_visitor.assigned_variables
        # print(self.assigned_variables)
        self.generic_visit(node)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if path.is_file():
        with open(path, 'r') as f:
            ca = CodeAnalyzer(f)
            ca.process_file()
            ca.print_errors()
    else:
        for file in sorted(list(path.iterdir())):
            if ".py" in file.name:
                # print(file)
                # filepath = input()
                with open(file, 'r') as f:
                    ca = CodeAnalyzer(f)
                    ca.process_file()
                    ca.print_errors()
