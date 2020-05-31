import sys
from lab2 import check_http_request_validity, parse_http_request, HttpRequestState, HttpRequestInfo

#######################################
# Leave the code below as is. (Tests)
# Read them to know how your classes
# are used.
#######################################


def lineno():
    return sys._getframe().f_back.f_lineno


def simple_http_parsing_test_cases():
    """
    Example test cases, do NOT modify this.
    If your code is correct, calling this function will have no effect.
    """
    client_addr = ("127.0.0.1", 9877)

    #######################################
    #######################################
    case = "Parse HTTP method."

    req_str = "GET / HTTP/1.0\r\nHost: www.google.edu\r\n\r\n"
    parsed = parse_http_request(client_addr, req_str)

    actual_value = parsed.method
    correct_value = "GET"
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    case = "Parse headers."

    # "Host: google.edu" header is added to the request.
    # note that the ":" is removed.
    actual_value = parsed.headers[0]        # note: headers is a list of lists
    correct_value = ["Host", "www.google.edu"]
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    case = "Add Default value of the port if it doesn't exist in the request."

    correct_value = str(80)
    actual_value = str(parsed.requested_port)
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")
    #######################################

    case = "Add requested host field."

    actual_value = parsed.requested_host
    correct_value = "www.google.edu" #changed from www.google.com --> because input string was www.google.edu
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "Convert full URL in request to relative path."

    actual_value = parsed.requested_path
    correct_value = "/"
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    case = "Add host header if a full HTTP path is used in request."

    actual_value = parsed.headers[0]
    correct_value = ["Host", "www.google.edu"]
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################
    case = "Parse HTTP headers"

    req_str = "GET / HTTP/1.0\r\nHost: www.google.com\r\nAccept: application/json\r\n\r\n"
    parsed = parse_http_request(client_addr, req_str)

    actual_value = str(len(parsed.headers))
    correct_value = str(2)
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################
    case = "convert HttpRequestInfo to a the corresponding HTTP request"
    # A request to www.google.com/ , note adding the ":" to headers
    # "Host" header comes first
    headers = [["Host", "www.google.com"], ["Accept", "application/json"]]
    req = HttpRequestInfo(client_addr, "GET",
                          "www.google.com", 80, "/", headers)

    http_string = "GET / HTTP/1.0\r\nHost: www.google.com\r\n"
    http_string += "Accept: application/json\r\n\r\n"

    correct_value = http_string
    actual_value = req.to_http_string()
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")


def simple_http_validation_test_cases():
    """
    Example test cases, do NOT modify this.
    If your code is correct, calling this function will have no effect.
    """
    case = "Parse a valid HTTP request."
    req_str = "GET / HTTP/1.0\r\nHost: www.google.edu\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.GOOD
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "Parse an invalid HTTP request (invalid method)"
    req_str = "GOAT / HTTP/1.0\r\nHost: www.google.edu\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.INVALID_INPUT
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "Parse an invalid HTTP request (not-supported method)"
    req_str = "HEAD / HTTP/1.0\r\nHost: www.google.edu\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.NOT_SUPPORTED
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "Parse an invalid HTTP request (relative path with no host header)"
    req_str = "HEAD / HTTP/1.0\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.INVALID_INPUT
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################
    case = "Parse an invalid HTTP request (bad header [no colon, no value])"
    req_str = "HEAD www.google.com HTTP/1.0\r\nAccept \r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.INVALID_INPUT
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################
    case = "Parse an invalid HTTP request (no HTTP version)"
    req_str = "HEAD / \r\nHost: www.google.edu\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.INVALID_INPUT
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value, actual_value)
    print(f"[success] {case}")

    #######################################
    #######################################
    case = "GET request with full URL in path returns GOOD"
    req_str = "GET http://google.edu/ HTTP/1.0\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.GOOD
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value.name, actual_value.name)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "GET request with relative path and host header returns GOOD"
    req_str = "GET / HTTP/1.0\r\nHost: google.edu\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.GOOD
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value.name, actual_value.name)
    print(f"[success] {case}")

    #######################################
    #######################################

    case = "Relative path without host header returns INVALID_INPUT"
    req_str = "GET / HTTP/1.0\r\n\r\n"

    actual_value = check_http_request_validity(req_str)
    correct_value = HttpRequestState.INVALID_INPUT
    assert correct_value == actual_value,\
        f"[Line {lineno()}] [failed] {case}"\
        " Expected ( %s ) got ( %s )" % (correct_value.name, actual_value.name)
    print(f"[success] {case}")


def main():
    ###################
    # Run tests
    ###################
    # Sorted by checklist order, feel free to comment/un-comment
    # any of those functions.
    try:
        simple_http_validation_test_cases()
        simple_http_parsing_test_cases()
    except AssertionError as e:
        print("Test case failed:\n", str(e))
        exit(-1)


if __name__ == "__main__":
    main()