# readstore-basic/frontend/streamlit/extensions.py

"""
This module contains various extension functions for the tCodeApp application.

Functions:
    - remove_sidebar():
        Remove the sidebar collapse control from the Streamlit app.
    - user_auth_basic(username: str, password: str) -> bool:
        Run basic authentication for the user against check_user_group
        API endpoint.
    - user_auth_status() -> bool:
        Verify access token in session state against backend endpoint.
    - get_jwt_token(username: str, password: str) -> Tuple[str,str]:
        Get a JWT token access and refresh tokens.
    - start_token_refresh_thread(): Start a thread to refresh the JWT token.

"""

import threading
import time
import os
import requests
import requests.auth as requests_auth
from urllib.parse import urlparse
from typing import Tuple
import json
import string
import re

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from pydantic import BaseModel
import pandas as pd

import uiconfig
import exceptions

APP_NAME = "app.py"

def df_not_empty(val) -> bool:
    if val is None:
        return False
    elif pd.isna(val):
        return False
    elif val == "":
        return False
    else:
        return True


def validate_charset(query_str: str):
    
    allowed = string.digits + string.ascii_lowercase + string.ascii_uppercase + '_-.@'
    allowed = set(allowed)
    
    return set(query_str) <= allowed


def validate_email(query_str: str) -> bool:
    """Validate email string

        Validate email string according to Django EMailValidator logic.
        
        Args:
            query_str: String to check if mail
        
        Returns:
            bool: True if query_str is email validated else False
    """
    
    user_regex = r"""(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)"""
    user_regex = re.compile(user_regex, re.IGNORECASE)
    
    domain_regex = (
        # max length for domain name labels is 63 characters per RFC 1034
        r"((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z",
        re.IGNORECASE,
    )
    domain_regex = re.compile(domain_regex[0], domain_regex[1])
       
    if "@" not in query_str or len(query_str) > 320:
        return False
    
    else:
        user_part, domain_part = query_str.rsplit("@", 1)
        
        if user_regex.match(user_part) and domain_regex.match(domain_part):
            return True
        else:
            return False


def switch_show_details():
    if not 'show_details' in st.session_state:
        st.session_state.show_details = True
    else: 
        st.session_state.show_details = not st.session_state.show_details

def refresh_page():
    st.cache_data.clear()
    st.rerun()

def remove_sidebar():
    """Remove the sidebar collapse control from the Streamlit app."""
    # Remove sidebar
    st.markdown(
        """
    <style>
        [data-testid="collapsedControl"] {
            display: none
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

def user_auth_basic(username: str, password: str) -> bool:
    """Run basic authentication against check_user_group API endpoint.

    Create HTTPBasicAuth object with username and password and send request to
    check_user_group API endpoint.
    Provice send user group defined in uiconfig.AUTH_USER_GROUP.

    Args:
        username: Username
        password: Plain text passwords

    Returns:
        bool: True if the user is authenticated, False otherwise.
    """

    # requets to user auth group
    login = requests_auth.HTTPBasicAuth(username, password)

    res = requests.get(os.path.join(uiconfig.BACKEND_API_ENDPOINT,
                                    "check_user_group/"),
                       auth=login,
                       params={"group": uiconfig.AUTH_USER_GROUP})

    if res.status_code == 200:
        return True
    else:
        return False
    
    
def user_auth_status() -> bool:
    """Verify access token in session state against backend endpoint.

    Method for validation of auth using JWT authentication (django simplejwt)
    Check if access_token is in session state and send request to
    verify token endpoint.

    Returns:
        bool: True if the user is authenticated, False otherwise.
    """

    if "access_token" in st.session_state:
        access_token = st.session_state["access_token"]
        url = os.path.join(uiconfig.BACKEND_API_ENDPOINT, "token/verify/")
        data = {"token": access_token}
        response = requests.post(url, data=data)

        if response.status_code == 200:
            return True
        else:
            return False
    else:
        return False


def get_jwt_token(username: str, password: str) -> Tuple[str, str]:
    """Get a JWT token access and refresh tokens.

    Get JWT token from backend API using username and password.
    Make API request to token endpoint with username and password.
    Used with django simplejwt authentication.

    Args:
        username: The username.
        password: The password.

    Returns:
        tuple: A tuple containing the access token and refresh token.

    Raises:
        exceptions.UIAppError: If the username or password is incorrect.
    """

    url = os.path.join(uiconfig.BACKEND_API_ENDPOINT, "token/")
    data = {"username": username, "password": password}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        access_token = response.json()["access"]
        refresh_token = response.json()["refresh"]

        return access_token, refresh_token
    else:
        raise exceptions.UIAppError("Username/password is incorrect")


def start_token_refresh_thread():
    """Start a thread to refresh the JWT token.

    Start a thread which periodially runs refresh_access_token
    method. Refeshes access_token of st.session_state

    add_script_run_ctx add thread to st script context thread.

    refresh_access_token function in thread executes API request to
    BACKEND_API_ENDPOINT. If response is 200, access token is updated

    uiconfig.ACCESS_TOKEN_REFESH_SECONDS global regulates how often
    the token is refreshed.

    Raises:
        exceptions.UIAppError if token cannot be refreshed.

    """

    def refresh_access_token(session_state):
        while True:
            url = os.path.join(uiconfig.BACKEND_API_ENDPOINT, "token/refresh/")
            data = {"refresh": session_state["refresh_token"]}
            response = requests.post(url, json=data, verify=False)

            if response.status_code == 200:
                access_token = response.json()["access"]
                session_state["access_token"] = access_token                
                session_state["jwt_auth_header"] = {"Authorization": "JWT " + access_token}
                
                time.sleep(uiconfig.ACCESS_TOKEN_REFESH_SECONDS)
            else:
                raise exceptions.UIAppError("Could not refresh token")

    t = threading.Thread(target=refresh_access_token, args=(st.session_state,))
    add_script_run_ctx(t)
    t.start()

def validate_url_scheme(url: str):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ["http", "https"]

def check_rest_api_endpoint(endpoint: str,
                            auth: requests_auth.HTTPBasicAuth | None = None,
                            headers: dict | None = None) -> bool:
    """If backend API endpoint can be reached.

    Provide the endpoint and the authentication credentials to check if the endpoint is reachable.
    Provide authentication credentials if the endpoint requires authentication.
    
    Example headers dict for JTW access token {"Authorization": "JWT " + access_token}
    
    Args:
        endpoint: The URL of the backend API endpoint.
        auth: The authentication credentials to use when accessing the endpoint.
        headers: Header for authentication for instance using JWT
    
    Returns:
        bool: True if the backend API endpoint is reachable, False otherwise.
    """
    
    assert validate_url_scheme(endpoint), "Invalid HTTP / HTTPS URL scheme."
    
    try:
        response = requests.head(endpoint, auth=auth, headers=headers)

        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.ConnectionError:
        return False

def validate_endpoints(endpoints: dict,
                       auth: requests_auth.HTTPBasicAuth | None = None,
                       headers : dict | None = None):
    """Validate REST Endpoints Required for the App.

    Args:
        endpoints: A dictionary of endpoints to validate.
            Key is name if endpoint, value is the endpoint URL.
        auth: HTTP Basic Auth. Defaults to None.
        headers: headers with Auth Token

    Raises:
        AssertionError: If the endpoint is invalid.
    """
    
    registered_urls = requests.get(uiconfig.BACKEND_API_ENDPOINT, auth=auth, headers=headers).json()
    
    for k, v in endpoints.items():
        if v not in registered_urls.values():
            # Try head request
            if not check_rest_api_endpoint(v, auth=auth, headers=headers):    
                raise exceptions.UIAppError(f"Endpoint {v} not found in registered endpoints.")

#region CRUD functions

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_request_to_df(endpoint: str,
                    validation_class: BaseModel,
                    auth: requests_auth.HTTPBasicAuth | None = None,
                    headers: dict | None = None,
                    query_params: dict | None = None) -> pd.DataFrame:
    
    """Convert validated HTTP GET response to dataframe.

    Execute HTTP GET request to endpoint with auth
    Validate response data using validation_class (pydantic model)
    Convert validated data to pandas and return as dataframe
    If response is empty, return empty dataframe with columns based
    on validation_class
    
    Args:
        endpoint: HTTP GET endpoint
        auth: HTTPBasicAuth object
        validation_class: Pydantic model for data validation
        query_params: Optional query parameters for the GET request

    Returns:
        pd.DataFrame: Dataframe with validated data
        
    Raises:
        assertionError if returned data is not a list or status
    """
    
    # HTTP Request
    if query_params:
        res = requests.get(endpoint, auth=auth, headers=headers, params=query_params)
    else:
        res = requests.get(endpoint, auth=auth, headers=headers)
    
    res_json = res.json()
    
    # data validation, returned json must be a list
    assert res.status_code == 200, f"Error: {res.status_code}"
    assert isinstance(res_json, list), "Returned data is not a list"
    
    # Data validation using pydantic
    data = [validation_class(**ele) for ele in res_json]
    
    # Empty list case: get dataframe with empty columns based on pydantic model
    # or cast validated data to dataframe
    if data == []:
        df = pd.DataFrame(columns=validation_class.__fields__.keys())
    else:
        df = pd.DataFrame([ele.dict() for ele in data])
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def detail_request_to_model(endpoint: str,
                            validation_class: BaseModel,
                            auth: requests_auth.HTTPBasicAuth | None = None,
                            headers: dict | None = None) -> BaseModel:
    """Convert validated HTTP detail GET response to pydantic Model.

    Execute HTTP GET request to endpoint detail view by PK with auth
    Validate response data using validation_class (pydantic model)
    Convert validated data to pandas and return as dataframe
    
    Args:
        endpoint: HTTP GET endpoint (must include PK) e.g. endpoint/12/
        auth: HTTPBasicAuth object
        validation_class: Pydantic model for data validation

    Returns:
        BaseModel: Pydantic model with validated data
        
    Raises:
        exceptions.UIAppError: If detail view not found
        assertionError if returned data is not a dict or status code != 200
    """
    
    res = requests.get(endpoint, auth=auth, headers=headers)
    res_json = res.json()
    
    # data validation, returned json must be a list
    assert res.status_code == 200, f"Error: {res.status_code}"
    assert isinstance(res_json, dict), "Returned data is not a dict"
    
    data = validation_class(**res_json)
    
    if (len(res_json) == 1) and ('detail' in res_json.keys()):
        raise exceptions.UIAppError('detail view not found')
    else:
        data = validation_class(**res_json)
        return data

def model_to_post_request(endpoint: str,
                        base_model: BaseModel,
                        auth: requests_auth.HTTPBasicAuth | None = None,
                        headers: dict | None = None,
                        method: str = 'json') -> int:
    
    """Convert Pydantic model to dictionary for POST request.

    Convert Pydantic model to dictionary for POST request.
    Remove fields with default values from the model.
    
    Args:
        base_model: Pydantic model
        endpoint: HTTP POST endpoint
        auth: Basic HTTP Authentication object
        headers: Request header containing token
        method: Method for payload in request, 'json' or 'data' 

    Returns:
        int: Primary key of the created object
        
    Raises:
        AssertionError return status code != 201
        """
    
    assert method in ['json', 'data'], "Method must be 'json' or 'data'"
    
    if method == 'json':
        res = requests.post(endpoint, 
                            json=base_model.dict(),
                            auth=auth,
                            headers=headers)
    else:
        res = requests.post(endpoint, 
                            data=base_model.model_dump(),
                            auth=auth,
                            headers=headers)
        
    if res.status_code != 201:
        raise AssertionError(f"Error: {res.status_code}, Message: {res.json()}")
    
    return int(res.json()['id'])

def model_to_put_request(endpoint: str,
                         pk: int,
                        base_model: BaseModel,
                        auth: requests_auth.HTTPBasicAuth | None = None,
                        headers: dict | None = None):
    """Convert Pydantic model to dictionary for PUT request.

    Convert Pydantic model to dictionary for PUT request.
    Remove fields with default values from the model.
    
    Args:
        base_model: Pydantic model
        endppoint: HTTP PUT endpoint

    Returns:
        dict: Dictionary with model data
        
    Raises:
        AssertionError return status code != 201
    """
    
    pk = int(pk)
    
    res = requests.put(endpoint + f'{pk}/', 
                        json=base_model.dict(),
                        auth=auth,
                        headers=headers)
    
    if res.status_code != 200:
        raise AssertionError(f"Error: {res.status_code}, Message: {res.json()}")
    

def dict_to_patch_request(endpoint: str,
                          model_data: dict,
                         auth: requests_auth.HTTPBasicAuth | None = None,
                         headers: dict | None = None):
    """Run PATCH request on endpoint with model data.

    PATCH endpoint with model data, where key represents field name
    and value represents updated value.
    
    Args:
        base_model: Pydantic model
        endpoint: HTTP PATCH endpoint
        
    Raises:
        AssertionError return status code != 200
    """
    
    res = requests.patch(endpoint, 
                        json=model_data,
                        auth=auth,
                        headers=headers)
    
    assert res.status_code == 200, f"Error: {res.status_code}"
    
def pk_to_delete_request(endpoint: str,
                         pk: int,
                        auth: requests_auth.HTTPBasicAuth | None = None,
                        headers: dict | None = None):
    """Run DELETE request on endpoint for pk.

    Args:
        endpoint: HTTP DELETE endpoint
        pk: primary key to delete
        auth: requests_auth.HTTPBasicAuth
        headers: Request heads, e.g. for auth
        
    Raises:
        AssertionError return status code != 204
    """
    # Esnure format
    pk = int(pk)
    
    res = requests.delete(endpoint + f'{pk}/',
                        auth=auth,
                        headers=headers)
    
    if not res.status_code in [203, 204]:
        raise AssertionError(f"Error: {res.status_code}, Message: {res.json()}")