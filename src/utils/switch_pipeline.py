
import json
from src.utils.logger import log

async def low_cost_priority(prediction_pipeline, data_dict, background_tasks, context_data):
    try:
        log("Using Low Cost Pipeline")
        # prediction_pipeline is async, so await it directly
        response = await prediction_pipeline(data_dict, background_tasks, context_data)
        response=json.dumps(response)
        # log(response)
        return response
    except Exception as prediction_error:
        log(f"Error: {prediction_error}\nUsing larger pipeline")
        return None

    