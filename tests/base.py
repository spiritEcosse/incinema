from unittest import IsolatedAsyncioTestCase

import pytest


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class BaseTest(IsolatedAsyncioTestCase):
    maxDiff = None

