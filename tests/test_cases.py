from django.test import TestCase


class AlgoliaSearchDjangoTestCase(TestCase):
    """A test case providing shortcuts methods"""

    @staticmethod
    def wait_for_tasks(index, *task_ids):
        """Wait all the provided task ids on the given index

        :param index: The index on the tasks were created
        :type index: AlgoliaIndex
        :param task_ids: A list of task that we want to wait for
        :type task_ids: list

        """

        for task_id in task_ids:
            index.wait_task(task_id)
