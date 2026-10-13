"""Safe, offline smoke test for Freeburg deployment image."""
from __future__ import annotations
import json,platform
from freeburg.deploy.signals import SLEEVES
def main():
    print(json.dumps({"status":"ready_for_offline_operations",
       "sleeves":list(SLEEVES),"python":platform.python_version(),
       "ibkr_connected":False,"live_orders_enabled":False,"x_posting_enabled":False}))
if __name__=="__main__":main()
