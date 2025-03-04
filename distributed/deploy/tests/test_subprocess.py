from __future__ import annotations

import pytest

from distributed import Client
from distributed.compatibility import WINDOWS
from distributed.deploy.subprocess import SubprocessCluster, SubprocessWorker
from distributed.utils_test import gen_test


@pytest.mark.skipif(WINDOWS, reason="distributed#7434")
@gen_test()
async def test_basic():
    async with SubprocessCluster(
        asynchronous=True,
        dashboard_address=":0",
        scheduler_kwargs={"idle_timeout": "5s"},
        worker_kwargs={"death_timeout": "5s"},
    ) as cluster:
        async with Client(cluster, asynchronous=True) as client:
            result = await client.submit(lambda x: x + 1, 10)
            assert result == 11
        assert cluster._supports_scaling
        assert "Subprocess" in repr(cluster)


@pytest.mark.skipif(WINDOWS, reason="distributed#7434")
@gen_test()
async def test_n_workers():
    async with SubprocessCluster(
        asynchronous=True, dashboard_address=":0", n_workers=2
    ) as cluster:
        async with Client(cluster, asynchronous=True) as client:
            assert len(cluster.workers) == 2
            result = await client.submit(lambda x: x + 1, 10)
            assert result == 11
        assert cluster._supports_scaling
        assert "Subprocess" in repr(cluster)


@pytest.mark.skipif(WINDOWS, reason="distributed#7434")
@gen_test()
async def test_scale_up_and_down():
    async with SubprocessCluster(
        n_workers=0,
        silence_logs=False,
        dashboard_address=":0",
        asynchronous=True,
    ) as cluster:
        async with Client(cluster, asynchronous=True) as c:

            assert not cluster.workers

            cluster.scale(2)
            await c.wait_for_workers(2)
            assert len(cluster.workers) == 2
            assert len(cluster.scheduler.workers) == 2

            cluster.scale(1)
            await cluster

            assert len(cluster.workers) == 1


@pytest.mark.skipif(
    not WINDOWS, reason="Windows-specific error testing (distributed#7434)"
)
def test_raise_on_windows():
    with pytest.raises(RuntimeError, match="not support Windows"):
        SubprocessCluster()

    with pytest.raises(RuntimeError, match="not support Windows"):
        SubprocessWorker(scheduler="tcp://127.0.0.1:8786")
