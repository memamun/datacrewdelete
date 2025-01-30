from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class DelegateWorkInput(BaseModel):
    """Input schema for DelegateWorkTool."""
    task: str = Field(
        ..., 
        description="The task to delegate"
    )
    context: str = Field(
        ..., 
        description="The context for the task"
    )
    coworker: str = Field(
        ..., 
        description="The role/name of the coworker to delegate to"
    )

class DelegateWorkTool(BaseTool):
    name: str = "Delegate work to coworker"
    description: str = (
        "Delegate a specific task to one of the following coworkers: "
        "Privacy Rights Request Composer\n\n"
        "The input to this tool should be:\n"
        "- task: A clear description of what needs to be done\n"
        "- context: All necessary information to complete the task\n"
        "- coworker: The name of the coworker to delegate to"
    )
    args_schema: Type[BaseModel] = DelegateWorkInput

    def _run(self, task: str, context: str, coworker: str) -> str:
        """Handle the tool execution."""
        try:
            logger.debug(f"Received inputs - task: {task}, context: {context}, coworker: {coworker}")
            
            # Handle dictionary-like strings
            if isinstance(task, dict) or (isinstance(task, str) and task.startswith('{')):
                try:
                    if isinstance(task, str):
                        import json
                        task_dict = json.loads(task)
                    else:
                        task_dict = task
                    task = task_dict.get('description', str(task_dict))
                except:
                    task = str(task)

            if isinstance(context, dict) or (isinstance(context, str) and context.startswith('{')):
                try:
                    if isinstance(context, str):
                        import json
                        context_dict = json.loads(context)
                    else:
                        context_dict = context
                    context = context_dict.get('description', str(context_dict))
                except:
                    context = str(context)
            
            # Ensure all inputs are strings
            task = str(task)
            context = str(context)
            coworker = str(coworker)
            
            logger.debug(f"Processed inputs - task: {task}, context: {context}, coworker: {coworker}")
            
            # Validate coworker
            valid_coworkers = ["Privacy Rights Request Composer"]
            if coworker not in valid_coworkers:
                return f"Invalid coworker specified: {coworker}. Valid options are: {', '.join(valid_coworkers)}"

            return (
                f"Task successfully delegated to {coworker}:\n"
                f"Task: {task}\n"
                f"Context: {context}"
            )
            
        except Exception as e:
            logger.error(f"Error in delegation: {e}", exc_info=True)
            return f"Error in delegation: {str(e)}" 