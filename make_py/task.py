TASKS = []


class Context:
    def __init__(self, sources, target):
        self.sources = sources
        self.target = target

    @property
    def source(self):
        return self.sources[0]


class Task:
    def __init__(self, matcher, handler, phony=False):
        self.matcher = matcher
        self.handler = handler
        self.phony = phony

    def run(self, ctx):
        self.handler(ctx)
