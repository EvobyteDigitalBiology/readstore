# readstore-basic/backend/api_tests/endpoint_test.py

from typing import List
from enum import Enum

import requests
import requests.auth as requests_auth

from zihelper import restapis

class HTTPOperations(Enum):
    GET = 'get'
    DETAIL = 'detail'
    POST = 'post'
    DELETE = 'delete'

class EndpointTest():
    
    def __init__(self,
                 endpoint: str,
                 data: dict,
                 auth: requests_auth.HTTPBasicAuth | None = None,
                 fk_endpoint: str | None = None,
                 fk_column: str | None = None,
                 verbose: bool = True,
                 operations: List[HTTPOperations] = [
                    HTTPOperations.GET,
                    HTTPOperations.DETAIL,
                    HTTPOperations.POST,
                    HTTPOperations.DELETE
                ]) -> None:
        
        self.endpoint = endpoint
        self.data = data
        self.auth = auth
        self.fk_endpoint = fk_endpoint
        self.fk_column = fk_column
        self.verbose = verbose
        self.operations = operations

        # Check if endpoint is valid
        assert restapis.check_rest_api_endpoint(endpoint, auth=auth),\
            f"Invalid endpoint: {endpoint}"
        
        if fk_endpoint:
            assert restapis.check_rest_api_endpoint(fk_endpoint, auth=auth),\
                f"Invalid endpoint: {fk_endpoint}"
                
            assert not fk_column is None, "Foreign key column not defined"
    
    def has_operation(self, operation: HTTPOperations) -> bool:
        return operation in self.operations
      
    def get_request(self):
        
        res = requests.get(self.endpoint, auth=self.auth)
        
        if self.verbose:
            print(res.json())
        
        assert res.status_code == 200, f"Error: {res.status_code}"
    
    def get_detail_request(self):
        
        res = requests.get(self.endpoint, auth=self.auth)
        detail_id = res.json()[0]['id']
        
        res = requests.get(self.endpoint + str(detail_id) + '/', auth=self.auth)
        
        if self.verbose:
            print(res.json())
        
        assert res.status_code == 200, f"Error: {res.status_code}"
    
    def post_request(self):
        
        data = self.data
        # Get fk id if required
        if self.fk_endpoint:
            res = requests.get(self.fk_endpoint, auth=self.auth)
            fk_id = res.json()[0]['id']
            data[self.fk_column] = fk_id
        
        res = requests.post(self.endpoint, json=data, auth=self.auth)
        
        if self.verbose:
            print(res.json())
        
        assert res.status_code == 201, f"Error: {res.status_code}"
    
    def delete_request(self):
        
        res = requests.get(self.endpoint, auth=self.auth)
        delete_id = res.json()[0]['id']
        
        res = requests.delete(self.endpoint + str(delete_id) + '/', auth=self.auth)
        
        # if self.verbose:
        #     print(res.json())
        
        assert res.status_code == 204, f"Error: {res.status_code}"
        
    def run_operations(self):
        
        for operation in self.operations:
            if operation == HTTPOperations.GET:
                self.get_request()
            elif operation == HTTPOperations.DETAIL:
                self.get_detail_request()
            elif operation == HTTPOperations.POST:
                self.post_request()
            elif operation == HTTPOperations.DELETE:
                self.delete_request()
            else:
                raise ValueError(f"Invalid operation: {operation}")
            
class EndpointTestManager():
    
    def __init__(self,
                 endpoint_tests: List[EndpointTest]) -> None:
        
        self.endpoint_tests = endpoint_tests
        
    def run_post_requests(self):
        
        for endpoint_test in self.endpoint_tests:
            if endpoint_test.has_operation(HTTPOperations.POST):
                endpoint_test.post_request()
    
    def run_get_requests(self):
        
        for endpoint_test in self.endpoint_tests:
            if endpoint_test.has_operation(HTTPOperations.GET):
                endpoint_test.get_request()
        
    def run_detail_requests(self):
            
        for endpoint_test in self.endpoint_tests:
            if endpoint_test.has_operation(HTTPOperations.DETAIL):
                endpoint_test.get_detail_request()

    #def run_put_request(self):
        

    def run_delete_requests(self):
        
        for endpoint_test in self.endpoint_tests[::-1]:
            if endpoint_test.has_operation(HTTPOperations.DELETE):
                endpoint_test.delete_request()
                
    def run_all_operations(self):
        
        self.run_post_requests()
        self.run_get_requests()
        self.run_detail_requests()
        self.run_delete_requests()