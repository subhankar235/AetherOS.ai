import logging
from typing import Any, Optional

logger = logging.getLogger("agents.supervisor.task_decomposer")


class Task:
    def __init__(
        self,
        agent: str,
        action: str,
        params: dict[str, Any],
        order: int = 0,
        depends_on: Optional[str] = None,
    ):
        self.agent = agent
        self.action = action
        self.params = params
        self.order = order
        self.depends_on = depends_on

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "action": self.action,
            "params": dict(self.params),
            "order": self.order,
            "depends_on": self.depends_on,
        }

    def __repr__(self) -> str:
        return f"Task(order={self.order}, agent={self.agent}, action={self.action})"


def decompose(raw_input: str, parsed_tasks: list[dict[str, Any]]) -> list[Task]:
    if not parsed_tasks:
        logger.info("No tasks to decompose — empty task list")
        return []

    tasks: list[Task] = []
    for idx, task_def in enumerate(parsed_tasks):
        task = Task(
            agent=task_def.get("agent", "unknown"),
            action=task_def.get("action", "unknown"),
            params=task_def.get("params", {}),
            order=idx,
            depends_on=task_def.get("depends_on"),
        )
        tasks.append(task)
        logger.debug(f"Decomposed task {idx}: {task}")

    return tasks


async def execute_sequentially(
    tasks: list[Task],
    stub_runner,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    previous_result: Optional[dict[str, Any]] = None

    for task in tasks:
        logger.info(f"Executing task {task.order}: {task.agent}/{task.action}")

        if task.depends_on and previous_result is None:
            error_msg = f"Task {task.order} depends on previous task which has no result"
            logger.error(error_msg)
            results.append({
                "task": task.to_dict(),
                "status": "error",
                "error": error_msg,
            })
            break

        try:
            merged_params = dict(task.params)
            if task.depends_on and previous_result is not None:
                merged_params["previous_result"] = previous_result

            result = await stub_runner(task.agent, task.action, merged_params)
            results.append({
                "task": task.to_dict(),
                "status": "completed",
                "result": result,
            })
            previous_result = result

        except Exception as exc:
            logger.exception(f"Task {task.order} ({task.agent}/{task.action}) failed: {exc}")
            results.append({
                "task": task.to_dict(),
                "status": "error",
                "error": str(exc),
            })
            break

    return results
