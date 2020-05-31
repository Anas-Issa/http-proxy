import socket
import sys
import os
import enum
import re
import threading

cache = {}


class HttpRequestInfo(object):
    def __init__(self, client_info, method: str, requested_host: str,
                 requested_port: int,
                 requested_path: str,
                 headers: list):
        self.method = method
        self.client_address_info = client_info
        self.requested_host = requested_host
        self.requested_port = requested_port
        self.requested_path = requested_path
        self.headers = headers

    def to_http_string(self):
        sanitize_http_request_object = sanitize_http_request(HttpRequestInfo(self.client_address_info, self.method,
                                                                             self.requested_host,
                                                                             self.requested_port,
                                                                             self.requested_path, self.headers))
        http_full_request = sanitize_http_request_object.method + sanitize_http_request_object.requested_path + "\r\n"
        for i in range(len(sanitize_http_request_object.headers)):
            http_full_request += sanitize_http_request_object.headers[i] + "\r\n"
        http_full_request += "\r\n"
        return http_full_request

    def to_byte_array(self, http_string):
        return bytes(http_string, "UTF-8")

    def display(self):
        print("**************************************************")
        print(f"Client:", self.client_address_info)
        print(f"Method:", self.method)
        print(f"Host:", self.requested_host)
        print(f"Port:", self.requested_port)
        stringified = [": ".join([k, v]) for (k, v) in self.headers]
        print("Headers:\n", "\n".join(stringified))
        print("**************************************************")


class HttpErrorResponse(object):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def to_http_string(self):
        return f'{self.code}: {self.message}'

    def to_byte_array(self, http_string):
        return bytes(http_string, "UTF-8")

    def display(self):
        print("**************************************************")
        print(self.to_http_string())
        print("**************************************************")


class HttpRequestState(enum.Enum):
    INVALID_INPUT = 0
    NOT_SUPPORTED = 1
    GOOD = 2
    PLACEHOLDER = -1


def entry_point(proxy_port_number):
    user_socket_setup(proxy_port_number)
    return None


def user_socket_setup(proxy_port_number):
    print(f'Starting HTTP proxy on port: {proxy_port_number}')

    # Initializing socket to receive request from the client(s) as a server
    proxy_as_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_as_server_socket.bind((socket.gethostname(), proxy_port_number))
    proxy_as_server_socket.listen(30)

    while True:
        user, address = proxy_as_server_socket.accept()

        # Creating threads to serve multiple clients
        serve_clients = threading.Thread(target=proxy_logic, args=(user, address))
        serve_clients.start()


def proxy_logic(user, address):
    # Receive a request
    full_request = user.recv(1024).decode("utf-8")

    # Validating, parsing then converting the http request to a string
    # Returning: http request(as string), http request(as object) and the error response if found
    ready_request_str, request_object, error_response = http_request_pipeline(address, full_request)

    if error_response is None:

        # Checking whether the reply in cache or not
        cashed_response = cache.get(get_caching_key(request_object))
        if cashed_response is None:
            # Fetching the response from destination
            response = get_response_from_destination(ready_request_str, request_object)
            # Saving the response in cache and sending it to the user
            cache[get_caching_key(request_object)] = response
            user.send(response)

        else:
            # Sending the cached response to the user
            user.send(cashed_response)
        user.close()
    else:
        # Error found in the http request --> sending the error to the user and exiting
        print('[ERROR] exiting...')
        user.send(error_response.to_byte_array(error_response.to_http_string()))
        user.close()


def get_response_from_destination(ready_request_str, request_object):

    # Initializing socket to send the request to the destination as a client
    proxy_as_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # try-except to handle any unreachable address
    try:
        proxy_as_client_socket.connect((request_object.requested_host, request_object.requested_port))
    except socket.gaierror:
        print("[ERROR] this address is not reachable (please check the address inserted)")
        return HttpRequestInfo.to_byte_array(None, "[ERROR] this address is not reachable (please check the address inserted)")
    proxy_as_client_socket.send(HttpRequestInfo.to_byte_array(None, ready_request_str))

    # Receiving the response from the destination
    full_response = b''
    while True:
        response_part = proxy_as_client_socket.recv(1024)
        if len(response_part) == 0:
            break
        full_response += response_part
    return full_response


# Returning the key to cache dictionary for the request
def get_caching_key(request_object):
    return f'{request_object.requested_host}{request_object.requested_path}'


def http_request_pipeline(source_addr, http_raw_data):

    # Returning HttpRequestError(INVALID_INPUT, NOT_SUPPORTED or GOOD)
    validity = check_http_request_validity(http_raw_data)
    if validity == HttpRequestState.INVALID_INPUT:
        error_response = HttpErrorResponse("400", "Bad request")
    elif validity == HttpRequestState.NOT_SUPPORTED:
        error_response = HttpErrorResponse("501", "Not implemented")
    else:
        error_response = None
        # Parsing the http request and returning the HttpRequestInfo object
        parsed = parse_http_request(source_addr, http_raw_data)
        HttpRequestInfo.display(parsed)
        http_request_str = parsed.to_http_string()
        return http_request_str, parsed, error_response

    # Returning error if found
    return None, None, error_response


def http_raw_data_manipulation(http_raw_data: str):

    # splitting the http request
    temp_input_list = http_raw_data.split(r'\r\n')
    if len(temp_input_list) == 1:
        temp_input_list = http_raw_data.split('\r\n')
    input_list = []

    # Removing any empty string in the list
    for i in range(len(temp_input_list)):
        if temp_input_list[i] != '':
            input_list.append(temp_input_list[i])

    # Checking if method, requested_path and http_version exist
    if len(input_list[0].split(' ')) == 3:
        method = input_list[0].split(' ')[0]
        requested_path = input_list[0].split(' ')[1]
        http_version = input_list[0].split(' ')[2]
    else:
        method = None
        requested_path = None
        http_version = None
    return method, requested_path, http_version, input_list


def parse_http_request(source_addr, http_raw_data) -> HttpRequestInfo:
    method, requested_path, http_version, input_list = http_raw_data_manipulation(http_raw_data)
    headers = []
    host_regex = "Host:"
    port_regex = r':\d+'

    # if Host is found
    if len(re.compile(host_regex).findall(http_raw_data)) == 1:
        requested_path = input_list[0].split(' ')[1]
        requested_host = re.findall('Host: (.*)[\r]', http_raw_data)[0]
        if len(re.findall('http://', requested_host)) == 1:
            requested_host = requested_host.split("//")[1]
    else:
        requested_host = input_list[0].split(' ')[1]
        if len(re.findall('http://', requested_host)) == 1:
            requested_host = requested_host.split("//")[1]

        if len(re.findall('/', requested_host)) != 0:
            requested_path = "/" + requested_host.split("/", 1)[1]
            requested_host = requested_host.split("/", 1)[0]
        else:
            requested_path = '/'

        if requested_host.endswith('/'):
            requested_host = requested_host[:-1]

    if len(re.compile(port_regex).findall(http_raw_data)) == 1:
        requested_port = int(re.findall(port_regex, requested_host)[0].split(':')[1])
        requested_host = requested_host.split(':')[0]
    else:
        requested_port = 80

    headers.append(['Host', requested_host])
    for i in range(2, len(input_list)):
        headers.append([input_list[i].split(': ')[0], input_list[i].split(': ')[1]])
    ret = HttpRequestInfo(source_addr, method, requested_host, requested_port, requested_path, headers)
    return ret


def check_http_request_validity(http_request_info: str) -> HttpRequestState:
    method, requested_path, http_version, input_list = http_raw_data_manipulation(http_request_info)
    http_verb = ['GET', 'POST', 'HEAD', 'PUT']

    if (method is None) or (requested_path is None) or (http_version is None):
        return HttpRequestState.INVALID_INPUT

    # checking headers:
    for i in range(1, len(input_list)):
        header_line = input_list[i].split(': ')
        if len(header_line) != 2:
            return HttpRequestState.INVALID_INPUT

    # Checking absolute and relative paths
    if len(re.compile('Host:').findall(http_request_info)) == 0 and input_list[0].split(" ")[1] == '/':
        return HttpRequestState.INVALID_INPUT

    # checking version:
    if http_version != "HTTP/1.0":
        return HttpRequestState.INVALID_INPUT

    # checking method
    if method not in http_verb:
        return HttpRequestState.INVALID_INPUT
    else:
        if method != "GET":
            return HttpRequestState.NOT_SUPPORTED
        else:
            return HttpRequestState.GOOD


def sanitize_http_request(request_info: HttpRequestInfo) -> HttpRequestInfo:
    temp_header = []
    for i in range(len(request_info.headers)):
        temp_header.append(request_info.headers[i][0] + ": " + request_info.headers[i][1])
    method = request_info.method + " "
    requested_path = request_info.requested_path + " " + "HTTP/1.0"
    ret = HttpRequestInfo(None, method, request_info.requested_host, request_info.requested_port, requested_path, temp_header)
    return ret


def get_arg(param_index, default=None):
    try:
        return sys.argv[param_index]
    except IndexError as e:
        if default:
            return default
        else:
            print(e)
            print(
                f"[FATAL] The comand-line argument #[{param_index}] is missing")
            exit(-1)  # Program execution failed.


def check_file_name():
    script_name = os.path.basename(__file__)
    import re
    matches = re.findall(r"(\d{4}_){2}lab2\.py", script_name)

    if not matches:
        print(f"[WARN] File name is invalid [{script_name}]")


def main():
    print("\n\n")
    print("*" * 50)
    print(f"[LOG] Printing command line arguments [{', '.join(sys.argv)}]")
    check_file_name()
    print("*" * 50)

    proxy_port_number = get_arg(1, 18888)
    entry_point(int(proxy_port_number))


if __name__ == "__main__":
    main()
