import shutil
# MySQL database service (replaces Supabase)
# Import inside functions to avoid circular imports

def sync_save_file_and_rewind(file_handle, file_path: str):
    """
    Synchronously saves the uploaded file content to disk and rewinds the file pointer.
    
    This function is designed to be executed in a separate thread via run_in_threadpool.
    """
    # Use copyfileobj to save the stream content
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file_handle, buffer)
    
    # CRITICAL: Rewind the pointer of the original UploadFile object's file handle.
    # This allows it to be read again later by the transcription service.
    file_handle.seek(0)


def sync_insert_transcription(data: dict):
    """
    Synchronously inserts data into the MySQL 'transcriptions' table.
    
    This function maintains the same interface as before for backward compatibility.
    It wraps the database service's sync_insert_transcription function.
    
    This function is designed to be executed in a separate thread via run_in_threadpool.
    """
    # Import here to avoid circular imports
    from src.database.db_functions import sync_insert_transcription as db_sync_insert
    return db_sync_insert(data)


def sync_update_is_correct(file_id: str):
    """
    Updates the 'iscorrect' field to True for the given file_id in the 'transcriptions' table.
    
    Args:
        file_id (str): The unique file identifier whose record should be updated.
    
    Returns:
        dict: The response from the update operation.
    """
    # Import here to avoid circular imports
    from src.database.db_functions import sync_update_transcription_is_correct
    return sync_update_transcription_is_correct(file_id)
