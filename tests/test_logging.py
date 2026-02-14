
# Ensure api is in path if needed (it is in current dir)
from api import logger

logger.info("test_event", status="sprint_3_1_success", complex={"key": "value"})
print("Test complete")
