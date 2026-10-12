from enum import Enum

class ResponseSignal(Enum):
    FILE_VALIDATED_SUCCESS = "file_validated_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    FILE_NOT_FOUND = "file_not_found"
    NO_FIELS_ERROR  = "not_found_files"
    NO_FILE_FOUND_FOR_THIS_ID = "no_file_found_for_this_id"

    PROCESSING_SUCCESS  = "Processing_success"
    PROCESSING_FAILED  = "Processing_failed"