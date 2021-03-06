import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_PLAN


class PlanTest(StripeResourceTest):
    async def test_create_plan(self):
        await aiostripe.Plan.create(**DUMMY_PLAN)

        self.requestor_mock.request.assert_called_with('post', '/v1/plans',
                                                       DUMMY_PLAN, None)

    async def test_delete_plan(self):
        p = aiostripe.Plan(id='pl_delete')

        await p.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/plans/pl_delete',
                                                       {}, None)

    async def test_update_plan(self):
        p = aiostripe.Plan(id='pl_update')
        p.name = 'Plan Name'

        await p.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/plans/pl_update',
                                                       {
                                                           'name': 'Plan Name',
                                                       }, None)


if __name__ == '__main__':
    unittest.main()
