#!/usr/bin/env python3

import argparse
import sys
import cmd
import re
import readline


class Facts:
    def __init__(self, subject):
        self.subject = subject
        self.subjects = {}
        self.facts = []

    def get_all_strings(self):
        factsL = []
        subjectsL = []
        subjectsL.append(self.subject)
        for fact in self.facts:
            factsL.append(fact)
        for subject, facts in self.subjects.items():
            subjectsL.append(subject)
            fgas = facts.get_all_strings()
            subjectsL.extend(fgas[0])
            factsL.extend(fgas[1])
        return subjectsL, factsL

    def register(self, fact, subject=None):
        if subject is None or subject == self.subject:
            self.facts.append(fact)
        else:
            # add fact to self.subjects[subject]
            # if self.subjects[subject] exists, if not create it as
            # a new Facts instance and add the fact that
            # the branch here is in the self.subjects.get
            self.register_subject(subject)
            self.subjects[subject].register(fact)

    def register_subject(self, subject):
        self.subjects[subject] = self.subjects.get(subject, Facts(subject))

    def search(self, term):
        occurences = {}
        # search all the facts known to the current knowledge base, 0 levels deep
        for fact in self.facts:
            if term in fact.lower():
                occurences[self.subject] = occurences.get(self.subject, []) + [fact]

        # search all the facts known to the sub-knowledge bases
        try:
            for subject, facts in self.subjects.items():
                results = facts.search(term)
                if results != {} and results != [{}]:
                    occurences[self.subject] = occurences.get(self.subject, {})
                    if isinstance(occurences[self.subject], list):
                        occurences[self.subject] += [results]
                    elif isinstance(occurences[self.subject], dict):
                        occurences[self.subject].update(results)
                # if len(results):
        except:
            print("Error occurred -------------------------------------------")
            raise
        return occurences

    def __repr__(self):
        return "<Facts instance with subject: {self.subject}>".format(self=self)


def matches(string, regex):
    pattern = re.compile(regex)

    if pattern.search(string) is None:
        return False
    else:
        return True


def save_to_file(interpreter, filepath_name):
    """returns None"""
    with open(filepath_name, "w") as fd:  # maybe use io.BytesIO
        fd.write(interpreter._hist)


def get_from_file(filepath_name):
    """returns a Facts object"""
    with open(filepath_name, "r") as fd:  # maybe use io.BytesIO
        facts = fd.read()
    return facts


def get_interpreter_from_file(filepath_name):
    facts = get_from_file(filepath_name)
    Int = FactInterpreter()
    Int.cmdqueue.extend(facts.splitlines())
    return Int


def parse_subject(line):
    """line should be in form
:subject: fact words and stuff"""
    _, subject, fact_words = line.split(":")
    fact_words = fact_words.strip()
    return subject, fact_words


class FactInterpreter(cmd.Cmd):
    prompt = "> "
    intro = "Fact recorder"

    def __init__(self, facts=None, *args, **kwargs):
        super(FactInterpreter, self).__init__(*args, **kwargs)
        self.stack = []
        self.facts = facts
        self.initcalled = False
        self._hist = []
        if facts is not None:
            self.root = facts
            self.initcalled = True

    def do_init(self, line):
        if not self.initcalled:
            subject, line = parse_subject(line)
            self.facts = Facts(subject)
            self.root = self.facts
            self.initcalled = True

    def initnotcalled(self):
        print("init needs to be called first")

    def do_import(self, line):
        subject, line = parse_subject(line)
        before_import = self.facts
        self.facts.register_subject(subject)
        self.stack.append(self.facts)
        self.facts = self.facts.subjects[subject]
        factstrings = get_from_file(line)
        for factS in factstrings.splitlines():
            self.onecmd(factS)
        self.facts = self.stack.pop()
        self.facts = before_import

    def do_push(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        try:
            subject, line = parse_subject(line)
        except ValueError:
            print("SyntaxError: push needs to be followed by the subject surrounded with colons i.e. \"push :subject matter: [fact words]*\"")

        print("->".join([self.facts.subject, subject]))
        self.facts.register_subject(subject)
        self.stack.append(self.facts)
        self.facts = self.facts.subjects[subject]
        if line not in ["", " "]:
            self.default(line)

    def help_push(self):
        print("pushes a new subject onto the input stack"
              "syntax: push :subject: [fact]")

    def do_pop(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        prev = self.facts.subject
        self.facts = self.stack.pop()
        print("->".join([prev, self.facts.subject]))

    def help_pop(self):
        print("pops the current subject off of the input stack"
              "syntax: pop")

    def do_pwd(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        if len(self.stack) !=0:
            print([f.subject for f in self.stack] + [self.facts.subject])
        else:
            print(self.facts.subject)

    def help_pwd(self):
        print("prints out the current context as a topic or chain of topics")

    do_context = do_pwd
    help_context = help_pwd

    def do_swap(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        self.do_pop(line)
        self.do_push(line)

    def help_swap(self):
        print("locally swaps topics to a topic of choice")

    def do_tag(self, line):
        """tags a fact or subject with a searchable term"""
        raise NotImplementedError

    def help_tag(self):
        pass

    def do_root(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        self.facts = self.root
        # while len(self.stack) > 1:
        #     self.stack.pop()
        self.stack = self.stack[:1]

    def help_root(self):
        print("sets the context to the global topic")

    def do_ls(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        if line.strip().startswith("all"):
            print('\n'.join(['\n'.join(ss) for ss in self.root.get_all_strings()]))
        else:
            print([key for key in self.facts.subjects])
            print("\n".join([fact for fact in self.facts.facts]))

    def do_search(self, line):
        if not self.initcalled:
            self.initnotcalled()
            return False
        # line should just be the search terms
        print(self.facts.search(line))

    def help_search(self):
        print("searches all the facts for term(s) and prints their contexts"
              "syntax: search [term]+")

    def do_end_and_save(self, line):
        save_to_file(line.strip())
        return True

    def default(self, line):
        print(line)
        if not self.initcalled:
            self.initnotcalled()
            return False
        if line.startswith(":"):
            subject, line = parse_subject(line)
            self.facts.register(line, subject)
        else:
            self.facts.register(line)

    def emptyline(self):
        pass

    def do_EOF(self, line):
        top_facts = self.stack[0] if len(self.stack) > 0 else self.facts
        if top_facts is not None:
            globals()['IntFacts'] = top_facts
        return True

    def postcmd(self, stop, line):
        self._hist.append(line)
        # print("postcmd")
        return stop


def test():
    with open("test.nb", 'r') as fd:
        testinput = fd.read().split("\n")
    Int = FactInterpreter()
    for line in testinput:
        Int.onecmd(line)
    Int.do_EOF('')

if __name__ == '__main__':
    version = "0.0.9"
    parser = argparse.ArgumentParser(description="record facts by topic.")
    # help(parser)
    parser.add_argument("--test", action="store_true", default=False)
    parser.add_argument("path", action="store", nargs='?', default=None, type=str, help="directory name to store notes")
    parser.add_argument("--save-at-end", action="store", nargs='?', const=True, default=False)
    parser.add_argument("--collect", action="append", nargs="*", default='')
    # print(parser.parse_args("/blah --save-at-end /blah2/blah.blah".split(" ")))
    print(len(sys.argv))
    args = parser.parse_args(sys.argv[1:])
    print(args)
    # test()

    global Int
    if not args.test:
        if args.save_at_end and args.path is None:
            raise parser.error("using --save-at-end requires a path")

        if args.path is not None:
            Int = get_interpreter_from_file(args.path)
        else:
            Int = FactInterpreter()

        try:
            print("getting here")
            Int.cmdloop()
        except:
            Int.do_EOF("")
            raise
        if args.save_at_end:
            save_to_file(Int, args.path)
        elif isinstance(args.save_at_end, str):
            save_to_file(Int, args.save_at_end)
    else:
        test()
