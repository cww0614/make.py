import sys
from queue import Queue
from threading import Thread


class Executor:
    def __init__(self, fs, tasks, jobs=1, silent=False):
        self.tasks = tasks
        self.fs = fs
        self.silent = silent
        self.jobs = jobs

        self.cancelled = False

    def resolve(self, queue, target):
        timestamp = self.fs.get_timestamp(target)
        file_exists = timestamp is not None
        if timestamp is None:
            timestamp = 0

        for task in self.tasks:
            ctx = task.matcher.match(target)
            if not ctx:
                continue

            should_run = False

            if len(ctx.sources) == 0:
                should_run = True

            for source in ctx.sources:
                ts = self.resolve(queue, source)
                if ts > timestamp:
                    should_run = True

            if should_run:
                queue.append((task, ctx))
                return sys.maxsize

            return timestamp

        if file_exists:
            return timestamp

        raise Exception(f"No rules to make target '{target}'")

    @staticmethod
    def queue_deduplication(queue):
        result = []
        seen = set()
        for (task, ctx) in queue:
            if ctx.target in seen:
                continue

            result.append((task, ctx))
            seen.add(ctx.target)

        return result

    def print_task(self, task, ctx, i, n):
        if not self.silent:
            file_list = ", ".join(ctx.sources)

            if len(file_list) == 0:
                file_list = "[]"

            name = ctx.target

            if not task.phony:
                file_list = "{} <= {}".format(ctx.target, file_list)
                name = task.handler.__name__

            print(
                "[{}/{}] {}: {}".format(
                    i + 1,
                    n,
                    name,
                    file_list,
                )
            )

    def worker(self, job_queue):
        while not self.cancelled and not job_queue.empty():
            i, n, task, ctx = job_queue.get()
            self.print_task(task, ctx, i, n)

            try:
                if not task.phony:
                    self.fs.make_parents(ctx.target)

                task.run(ctx)
            except Exception as e:
                self.cancelled = True
                raise e
            finally:
                job_queue.task_done()

    def execute(self, targets):
        queue = []

        for target in targets:
            self.resolve(queue, target)

        queue = self.queue_deduplication(queue)

        job_queue = Queue()

        self.cancelled = False
        n = len(queue)
        for i, (task, ctx) in enumerate(queue):
            job_queue.put((i, n, task, ctx))

        threads = [
            Thread(target=self.worker, args=(job_queue,)) for _ in range(self.jobs)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()
