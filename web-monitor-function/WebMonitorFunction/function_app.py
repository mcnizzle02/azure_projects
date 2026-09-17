import azure.functions as func
import logging
import requests
import time

app = func.FunctionApp()

TARGET_URL = "https://www.microsoft.com"  # swap in whatever site you want to monitor

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def CheckWebsite(myTimer: func.TimerRequest) -> None:
    start_time = time.time()
    try:
        response = requests.get(TARGET_URL, timeout=10)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logging.info(f"SiteCheck | url={TARGET_URL} status={response.status_code} response_time_ms={elapsed_ms}")
    except requests.exceptions.RequestException as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logging.error(f"SiteCheck | url={TARGET_URL} status=DOWN error={str(e)} response_time_ms={elapsed_ms}")