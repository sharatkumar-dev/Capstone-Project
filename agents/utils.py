import time
import logging

logger = logging.getLogger("TaxAssistantApp.ModelCall")

def call_gemini_with_fallback(client, method_name: str, model_args: dict, fallback_models=None):
    """
    Executes a Gemini API model call with built-in retry logic (exponential backoff)
    for 429 and 503 errors, and automatic fallback across alternative models.
    """
    if fallback_models is None:
        # Cascade through available flash and flash-lite models
        fallback_models = [
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-3.5-flash"
        ]
        
    last_exception = None
    
    for model in fallback_models:
        # Set the model parameter for this attempt
        model_args['model'] = model
        retries = 3
        backoff = 2.0 # seconds
        
        for attempt in range(retries):
            try:
                logger.info("Attempting Gemini call using model '%s' (attempt %d/%d)...", model, attempt + 1, retries)
                method = getattr(client.models, method_name)
                response = method(**model_args)
                logger.info("Gemini call succeeded with model '%s'", model)
                return response
            except Exception as e:
                last_exception = e
                err_msg = str(e).lower()
                
                # Check if error is retryable (429 or 503)
                is_retryable = (
                    "429" in err_msg or 
                    "503" in err_msg or 
                    "resource_exhausted" in err_msg or 
                    "unavailable" in err_msg
                )
                
                if is_retryable and attempt < retries - 1:
                    logger.warning("Retryable error encountered on model '%s': %s. Retrying in %.1fs...", model, str(e), backoff)
                    time.sleep(backoff)
                    backoff *= 2.0 # Exponential backoff
                else:
                    logger.warning("Model '%s' failed on attempt %d: %s", model, attempt + 1, str(e))
                    break # Break retry loop, proceed to next fallback model
                    
    # If all models and all retry attempts fail
    logger.error("All fallback models and retries were exhausted.")
    raise last_exception
