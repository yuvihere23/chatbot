import subprocess
import tempfile
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScriptExecutor:
    def execute(self, script: str) -> Any:
        """Execute Python script and return parsed results"""
        if not script or not isinstance(script, str):
            raise ValueError("Invalid script provided for execution")

        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as tf:
            try:
                tf.write(script)
                tf.flush()
                
                logger.debug(f"Executing script from {tf.name}")
                result = subprocess.run(
                    ['python', tf.name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                logger.debug(f"Script stdout: {result.stdout[:200]}...")
                
                if result.returncode != 0:
                    error_msg = result.stderr or "Script execution failed"
                    logger.error(f"Script failed: {error_msg}")
                    raise RuntimeError(error_msg)
                
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON output: {result.stdout[:200]}...")
                    raise ValueError(f"Invalid script output: {str(e)}")
                    
            except subprocess.TimeoutExpired:
                logger.error("Script execution timed out")
                raise RuntimeError("Execution timeout")
            except Exception as e:
                logger.error(f"Execution error: {str(e)}")
                raise RuntimeError(f"Script execution failed: {str(e)}")
            finally:
                try:
                    tf.close()
                except Exception:
                    pass