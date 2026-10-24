"""Gate Test on the host: the agent loads this file and answers its routes with the same token as its own"""
from dash_sdk import get

@get("/zz-gate-test/hello", quiet=True)
def hello(q):
    return {"hello": "Gate Test is running on the host"}
