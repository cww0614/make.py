import sys
from queue import Queue
from threading import Thread, Lock


class JobPool:
    def __init__(self):
        self.jobs = {}
        self.job_no_lock = Lock()
        self._next_job_no = 1

    def get(self, target):
        return self.jobs.get(target)

    def create(self, queue, target, task, ctx):
        job = Job(self, queue, target, task, ctx)
        self.jobs[target] = job
        return job

    def next_job_no(self):
        with self.job_no_lock:
            no = self._next_job_no
            self._next_job_no += 1
            return no

    def total_job_no(self):
        return len(self.jobs)


class Job:
    all_jobs = {}
    job_no_lock = Lock()
    _next_job_no = 1

    def __init__(self, pool, queue, target, task, ctx):
        self.queue = queue
        self.target = target
        self.task = task
        self.ctx = ctx

        self.depends_on = {}
        self.depended_by = []
        self._job_no = None

        self.pool = pool

    def add_dependency(self, job):
        id = len(self.depends_on)
        self.depends_on[id] = job
        job.depended_by.append((id, self))

    def done(self):
        for id, dep in self.depended_by:
            dep.dependency_done(id)
        self.depended_by = []

    def dependency_done(self, id):
        self.depends_on.pop(id, None)
        self.try_enqueue()

    def job_no(self):
        if self._job_no is None:
            self._job_no = self.pool.next_job_no()

        return self._job_no

    def try_enqueue(self):
        if len(self.depends_on) > 0:
            return

        self.queue.put((self, self.task, self.ctx))


class Executor:
    def __init__(self, fs, job_pool, tasks, jobs=1, silent=False):
        self.fs = fs
        self.job_pool = job_pool

        self.tasks = tasks
        self.silent = silent
        self.jobs = jobs

        self.cancelled = False

    def resolve(self, queue, target):
        job = self.job_pool.get(target)
        if job:
            return sys.maxsize, job

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

            dependencies = []
            for source in ctx.sources:
                ts, job = self.resolve(queue, source)
                if ts > timestamp:
                    should_run = True
                if job:
                    dependencies.append(job)

            if should_run:
                job = self.job_pool.create(queue, target, task, ctx)
                for dep in dependencies:
                    job.add_dependency(dep)
                job.try_enqueue()
                return sys.maxsize, job

            return timestamp, None

        if file_exists:
            return timestamp, None

        raise Exception(f"No rules to make target '{target}'")

    def print_task(self, task, ctx, i, n):
        if not self.silent:
            file_list = ", ".join(ctx.sources)

            if len(file_list) == 0:
                file_list = "[]"

            name = ctx.target

            if not task.phony:
                file_list = "{} <- {}".format(ctx.target, file_list)
                name = task.handler.__name__

            print(
                "[{}/{}] {}: {}".format(
                    i,
                    n,
                    name,
                    file_list,
                )
            )

    def worker(self, job_queue):
        while not self.cancelled and not job_queue.empty():
            job, task, ctx = job_queue.get()
            self.print_task(task, ctx, job.job_no(), job.pool.total_job_no())

            try:
                if not task.phony:
                    self.fs.make_parents(ctx.target)

                task.run(ctx)
            except Exception as e:
                self.cancelled = True
                raise e
            finally:
                job.done()
                job_queue.task_done()

    def execute(self, target):
        queue = Queue()
        self.resolve(queue, target)

        threads = [Thread(target=self.worker, args=(queue,)) for _ in range(self.jobs)]

        self.cancelled = False
        for t in threads:
            t.start()

        for t in threads:
            t.join()
