"""RunLogStore that writes to the standard logger. Replace with a persistent store later."""

import logging

from etl.domain.results import StageResult

logger = logging.getLogger("etl.run")


class LoggingRunLogStore:
    def record_stage(self, result: StageResult) -> None:
        logger.info(
            "stage=%s rows_in=%d rows_out=%d rejected=%d files_failed=%d",
            result.stage,
            result.rows_in,
            result.rows_out,
            result.rows_rejected,
            result.files_failed,
        )
