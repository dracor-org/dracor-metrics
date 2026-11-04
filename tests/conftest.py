import logging

import pytest


@pytest.fixture(autouse=True)
def fail_on_unhandled_errors(request, caplog):
    """Fails tests whose requests ran into an unhandled error

    The error middleware answers these with a 500, so the test itself would
    only see the status code. This shows the traceback instead.
    """
    yield
    if request.node.get_closest_marker("unhandled_errors"):
        return
    formatter = logging.Formatter()
    errors = [
        formatter.formatException(record.exc_info)
        for record in caplog.get_records("call")
        if record.name == "uvicorn.error" and record.exc_info
    ]
    if errors:
        pytest.fail("Unhandled error in request:\n" + "\n".join(errors), pytrace=False)
