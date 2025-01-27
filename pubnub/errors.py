PNERR_CLIENT_TIMEOUT = "Client Timeout"
PNERR__TIMEOUT = "Timeout Occurred"
PNERR_REQUEST_CANCELLED = "HTTP Client Error"
# TODO: clarify to not confuse with 4xx and 5xx http erros
PNERR_HTTP_ERROR = "HTTP Error"
PNERR_CONNECTION_ERROR = "Connection Error"
PNERR_TOO_MANY_REDIRECTS_ERROR = "Too many redirects"
# For 5xx server responses
PNERR_SERVER_ERROR = "HTTP Server Error"
# For 4xx server responses
PNERR_CLIENT_ERROR = "HTTP Client Error"
PNERR_UNKNOWN_ERROR = "Unknown Error"
PNERR_CHANNEL_MISSING = "Channel missing"
PNERR_CHANNELS_MISSING = "Channels missing"
PNERR_GROUP_MISSING = "Channel group missing"
PNERR_MESSAGE_MISSING = "Message missing"
PNERR_SUBSCRIBE_KEY_MISSING = "Subscribe key not configured"
PNERR_SECRET_KEY_MISSING = "Secret key is not configured"
PNERR_PUBLISH_KEY_MISSING = "Publish key not configured"
PNERR_PUBLISH_META_WRONG_TYPE = "Publish meta should be dict"
PNERR_DEFERRED_NOT_IMPLEMENTED = (
    "Deferred endpoint call is not implemented by this platform"
)
PNERR_JSON_DECODING_FAILED = "JSON decoding failed"
PNERR_JSON_NOT_SERIALIZABLE = "Trying to publish not JSON serializable object"
PNERR_CHANNEL_OR_GROUP_MISSING = "Channel or group missing"
PNERR_STATE_MISSING = "State missing or not a dict"
PNERR_UUID_MISSING = "uuid missing or not a string"
PNERR_STATE_SETTER_FOR_GROUPS_NOT_SUPPORTED_YET = (
    "State setter for channel groups is not supported yet"
)
PNERR_PUSH_DEVICE_MISSING = "Device ID is missing for push operation"
PNERROR_PUSH_TYPE_MISSING = "Push Type is missing"
PNERR_PAM_NO_FLAGS = "At least one flag should be specified"
PNERR_PAM_INVALID_ARGUMENTS = "Invalid arguments"
PNERR_RESOURCES_MISSING = "Resources missing"
PNERR_TTL_MISSING = "TTL missing"
PNERR_INVALID_META = "Invalid meta parameter"
PNERR_INVALID_ACCESS_TOKEN = "Invalid access token"
PNERR_MESSAGE_ACTION_MISSING = "Message action is missing"
PNERR_MESSAGE_ACTION_TYPE_MISSING = "Message action type is missing"
PNERR_MESSAGE_ACTION_VALUE_MISSING = "Message action value is missing"
PNERR_MESSAGE_TIMETOKEN_MISSING = "Message timetoken is missing"
PNERR_MESSAGE_ACTION_TIMETOKEN_MISSING = "Message action timetoken is missing"
PNERR_HISTORY_MESSAGE_ACTIONS_MULTIPLE_CHANNELS = (
    "History can return message action data for a single channel only. "
    "Either pass a single channel or disable the include_message_action"
    "s flag. "
)

PNERR_PUSH_TOPIC_MISSING = (
    "Push notification topic is missing. Required only if push type is APNS2."
)

PNERR_FILE_OBJECT_MISSING = "File object is missing."
PNERR_FILE_NAME_MISSING = "File name is missing."
PNERR_FILE_ID_MISSING = "File id is missing."
PNERR_SPACE_MISSING = "Space missing"
PNERR_SPACES_MISSING = "Spaces missing"

PNERR_USER_ID_MISSING = "user_id missing or not a string"
PNERR_USER_SPACE_PAIRS_MISSING = "User/Space pair is missing"
PNERR_MISUSE_OF_USER_AND_USERS = "user_id and users should not be used together"
PNERR_MISUSE_OF_SPACE_AND_SPACES = "space_id and spaces should not be used together"
PNERR_MISUSE_OF_USER_AND_SPACE = "user_id and space_id should not be used together"
PNERR_INVALID_USER = "Provided user is not valid instance of User"
PNERR_INVALID_SPACE = "Provided space is not valid instance of Space"
