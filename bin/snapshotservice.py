#!/usr/bin/env python3

import time
import snapshot
import cvcontrol
import logging
import schedule
import statesync
from cvutils import (
    get_ctx,
)

def main(ctx):
    try:
        if ctx.get("statesync_snapshot"):
            statesync.main(ctx)
            snapshot.wait_for_sync(ctx)
        logging.info(f"Creating lz4 snapshot")
        snapshots_dir = ctx.get("snapshots_dir")
        data_dir = ctx.get("data_dir")
        cosmprund_enabled = ctx.get("cosmprund_enabled")
        cvcontrol.stop_process('cosmovisor')
        snapshot.create_snapshot(snapshots_dir, data_dir, cosmprund_enabled)
        cvcontrol.start_process('cosmovisor')
        logging.info(f"Finished lz4 snapshot")
    except Exception as e:
        logging.error(f"Failed to creat snapshot")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ctx = get_ctx()
    schedule.every().day.at("06:00", "US/Central").do(main, ctx)
    while True:
        schedule.run_pending()
        time.sleep(600)