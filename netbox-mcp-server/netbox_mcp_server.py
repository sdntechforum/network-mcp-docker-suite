"""
NetBox MCP Server

A Model Context Protocol (MCP) server that provides comprehensive access to NetBox DCIM/IPAM functionality.
This server allows AI assistants and other MCP clients to interact with NetBox for network
documentation and infrastructure management.

Features:
- Complete CRUD operations for NetBox objects
- Device and infrastructure management
- IP address management (IPAM)
- Site and location tracking
- Circuit and provider management
- Bulk operations support

Environment Variables:
- NETBOX_URL: Required. Your NetBox instance URL
- NETBOX_TOKEN: Required. Your NetBox API token
- MCP_PORT: Optional. Port for MCP server. Defaults to 8001
- MCP_HOST: Optional. Host for MCP server. Defaults to localhost

Author: Patrick Mosimann
"""

import abc
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests
from fastmcp import FastMCP

# ---- Environment Variables ----
def load_dotenv_file(env_file: str = ".env") -> bool:
    """Load environment variables from a .env file"""
    env_path = Path(env_file)
    
    if not env_path.exists():
        print(f"⚠️  .env file not found at {env_path.absolute()}")
        print(f"📋 Using environment variables or defaults")
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
        
        print(f"✅ Loaded environment from {env_file}")
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

# Load .env file first
load_dotenv_file()

# Get configuration from environment
netbox_url = os.getenv("NETBOX_URL")
netbox_token = os.getenv("NETBOX_TOKEN")
netbox_verify_ssl = os.getenv("NETBOX_VERIFY_SSL", "true").lower() in ("true", "1", "yes")
mcp_port = int(os.getenv("MCP_PORT", "8001"))
mcp_host = os.getenv("MCP_HOST", "localhost")

# Validate required configuration
if not netbox_url:
    print("❌ NETBOX_URL not configured!")
    print("📋 Please set your NetBox URL in .env file")
    print("   Example: NETBOX_URL=https://netbox.example.com")
    exit(1)

if not netbox_token:
    print("❌ NETBOX_TOKEN not configured!")
    print("📋 Please set your NetBox API token in .env file")
    print("   Example: NETBOX_TOKEN=your_token_here")
    exit(1)

print(f"✅ NetBox URL: {netbox_url}")
print(f"✅ NetBox token configured")
print(f"🔒 SSL verification: {'enabled' if netbox_verify_ssl else 'disabled'}")
print(f"🌐 MCP Server will run on: http://{mcp_host}:{mcp_port}")

class NetBoxClientBase(abc.ABC):
    """
    Abstract base class for NetBox client implementations.
    
    This class defines the interface for CRUD operations that can be implemented
    either via the REST API or directly via the ORM in a NetBox plugin.
    """
    
    @abc.abstractmethod
    def get(self, endpoint: str, id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieve one or more objects from NetBox."""
        pass
    
    @abc.abstractmethod
    def create(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new object in NetBox."""
        pass
    
    @abc.abstractmethod
    def update(self, endpoint: str, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing object in NetBox."""
        pass
    
    @abc.abstractmethod
    def delete(self, endpoint: str, id: int) -> bool:
        """Delete an object from NetBox."""
        pass
    
    @abc.abstractmethod
    def bulk_create(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple objects in NetBox."""
        pass
    
    @abc.abstractmethod
    def bulk_update(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update multiple objects in NetBox."""
        pass
    
    @abc.abstractmethod
    def bulk_delete(self, endpoint: str, ids: List[int]) -> bool:
        """Delete multiple objects from NetBox."""
        pass


class NetBoxRestClient(NetBoxClientBase):
    """NetBox client implementation using the REST API."""
    
    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        """Initialize the REST API client."""
        self.base_url = url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def _build_url(self, endpoint: str, id: Optional[int] = None) -> str:
        """Build the full URL for an API request."""
        endpoint = endpoint.strip('/')
        if id is not None:
            return f"{self.api_url}/{endpoint}/{id}/"
        return f"{self.api_url}/{endpoint}/"
    
    def get(self, endpoint: str, id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieve one or more objects from NetBox via the REST API."""
        url = self._build_url(endpoint, id)
        response = self.session.get(url, params=params, verify=self.verify_ssl)
        response.raise_for_status()
        
        data = response.json()
        if id is None and 'results' in data:
            return data['results']
        return data
    
    def create(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new object in NetBox via the REST API."""
        url = self._build_url(endpoint)
        response = self.session.post(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def update(self, endpoint: str, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing object in NetBox via the REST API."""
        url = self._build_url(endpoint, id)
        response = self.session.patch(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, id: int) -> bool:
        """Delete an object from NetBox via the REST API."""
        url = self._build_url(endpoint, id)
        response = self.session.delete(url, verify=self.verify_ssl)
        response.raise_for_status()
        return response.status_code == 204
    
    def bulk_create(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple objects in NetBox via the REST API."""
        url = f"{self._build_url(endpoint)}bulk/"
        response = self.session.post(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def bulk_update(self, endpoint: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update multiple objects in NetBox via the REST API."""
        url = f"{self._build_url(endpoint)}bulk/"
        response = self.session.patch(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()
    
    def bulk_delete(self, endpoint: str, ids: List[int]) -> bool:
        """Delete multiple objects from NetBox via the REST API."""
        url = f"{self._build_url(endpoint)}bulk/"
        data = [{"id": id} for id in ids]
        response = self.session.delete(url, json=data, verify=self.verify_ssl)
        response.raise_for_status()
        return response.status_code == 204


# Initialize NetBox client
client = NetBoxRestClient(
    url=netbox_url,
    token=netbox_token,
    verify_ssl=netbox_verify_ssl
)

print("[DEBUG] Creating comprehensive NetBox MCP server...")

# Create MCP server instance early
mcp = FastMCP("NetBox API Server")

# ---- DCIM Tools ----
@mcp.tool()
def get_sites(limit: int = 50, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Get sites from NetBox DCIM. Optionally filter with params."""
    try:
        query_params = {"limit": limit}
        if params:
            query_params.update(params)
        return {"success": True, "data": client.get("dcim/sites", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_site_by_id(site_id: int) -> Dict[str, Any]:
    """Get a specific site by ID."""
    try:
        return {"success": True, "data": client.get("dcim/sites", id=site_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_site(name: str, slug: str, status: str = "active", description: str = "") -> Dict[str, Any]:
    """Create a new site in NetBox."""
    try:
        site_data = {
            "name": name,
            "slug": slug,
            "status": status,
            "description": description
        }
        return {"success": True, "data": client.create("dcim/sites", site_data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_devices(limit: int = 50, site_id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get devices from NetBox DCIM. Optionally filter by site or other params."""
    try:
        query_params = {"limit": limit}
        if site_id:
            query_params["site_id"] = site_id
        if params:
            query_params.update(params)
        return {"success": True, "data": client.get("dcim/devices", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_device_by_id(device_id: int) -> Dict[str, Any]:
    """Get a specific device by ID."""
    try:
        return {"success": True, "data": client.get("dcim/devices", id=device_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_device(name: str, device_type_id: int, site_id: int, status: str = "active") -> Dict[str, Any]:
    """Create a new device in NetBox."""
    try:
        device_data = {
            "name": name,
            "device_type": device_type_id,
            "site": site_id,
            "status": status
        }
        return {"success": True, "data": client.create("dcim/devices", device_data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_device_types(limit: int = 50, manufacturer_id: Optional[int] = None) -> Dict[str, Any]:
    """Get device types from NetBox DCIM."""
    try:
        query_params = {"limit": limit}
        if manufacturer_id:
            query_params["manufacturer_id"] = manufacturer_id
        return {"success": True, "data": client.get("dcim/device-types", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---- IPAM Tools ----
@mcp.tool()
def get_ip_addresses(limit: int = 50, vrf_id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get IP addresses from NetBox IPAM."""
    try:
        query_params = {"limit": limit}
        if vrf_id:
            query_params["vrf_id"] = vrf_id
        if params:
            query_params.update(params)
        return {"success": True, "data": client.get("ipam/ip-addresses", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_ip_address(address: str, status: str = "active", description: str = "") -> Dict[str, Any]:
    """Create a new IP address in NetBox."""
    try:
        ip_data = {
            "address": address,
            "status": status,
            "description": description
        }
        return {"success": True, "data": client.create("ipam/ip-addresses", ip_data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_prefixes(limit: int = 50, vrf_id: Optional[int] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get prefixes from NetBox IPAM."""
    try:
        query_params = {"limit": limit}
        if vrf_id:
            query_params["vrf_id"] = vrf_id
        if params:
            query_params.update(params)
        return {"success": True, "data": client.get("ipam/prefixes", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_vlans(limit: int = 50, site_id: Optional[int] = None) -> Dict[str, Any]:
    """Get VLANs from NetBox IPAM."""
    try:
        query_params = {"limit": limit}
        if site_id:
            query_params["site_id"] = site_id
        return {"success": True, "data": client.get("ipam/vlans", params=query_params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---- Search and Query Tools ----
@mcp.tool()
def search_objects(endpoint: str, query: str, limit: int = 25) -> Dict[str, Any]:
    """Search for objects in NetBox using the 'q' parameter."""
    try:
        params = {"q": query, "limit": limit}
        return {"success": True, "data": client.get(endpoint, params=params)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def update_object(endpoint: str, object_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing object in NetBox."""
    try:
        return {"success": True, "data": client.update(endpoint, object_id, data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def delete_object(endpoint: str, object_id: int) -> Dict[str, Any]:
    """Delete an object from NetBox."""
    try:
        success = client.delete(endpoint, object_id)
        return {"success": success, "message": f"Object {object_id} deleted" if success else "Deletion failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---- Custom Scripts Tools ----
@mcp.tool()
def get_custom_scripts() -> Dict[str, Any]:
    """
    List all available custom scripts in NetBox.
    
    Custom scripts are user-defined workflows that can automate complex operations
    like provisioning sites, configuring devices, or running compliance checks.
    Each script has a name, description, and required parameters (vars).
    
    Returns:
        Dict with success status and list of available scripts with their metadata:
        - id: Script ID
        - name: Script class name (e.g., "CreateSiteAndLocations")
        - description: Human-readable description of what the script does
        - vars: Dictionary of input variables and their types
        - is_executable: Whether the script can be executed
        - result: Last execution result (if any)
    
    Example:
        scripts = get_custom_scripts()
        for script in scripts["data"]:
            print(f"{script['name']}: {script['description']}")
            print(f"Required parameters: {script['vars']}")
    """
    try:
        response = client.get("extras/scripts")
        
        # Format the response for better readability
        if isinstance(response, list):
            scripts_list = response
        elif isinstance(response, dict) and 'results' in response:
            scripts_list = response['results']
        else:
            scripts_list = []
        
        # Enhance script info for AI understanding
        enhanced_scripts = []
        for script in scripts_list:
            enhanced_scripts.append({
                "id": script.get("id"),
                "name": script.get("name"),
                "description": script.get("description", "No description available"),
                "display": script.get("display"),
                "module": script.get("module"),
                "vars": script.get("vars", {}),
                "is_executable": script.get("is_executable", False),
                "last_result": script.get("result")
            })
        
        return {
            "success": True,
            "count": len(enhanced_scripts),
            "data": enhanced_scripts
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_script_variables(script_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a script's required variables.
    
    This tool explains what each variable expects, especially for ObjectVar types
    which require looking up object IDs before execution.
    
    Args:
        script_id: The script ID
    
    Returns:
        Dict with variable information and guidance on how to provide values
    
    Example:
        # Get variables for CreateSiteAndLocations (ID 17)
        vars_info = get_script_variables(script_id=17)
        # Shows: tenant (ObjectVar) - needs tenant ID, use search_tenants()
        #        region (ObjectVar) - needs region ID, use search_regions()
        #        site_name (StringVar) - provide as string
        #        number_of_floors (IntegerVar) - provide as integer
    """
    try:
        # Get the script details
        script = client.get("extras/scripts", id=script_id)
        
        if not isinstance(script, dict):
            return {"success": False, "error": "Script not found"}
        
        vars_dict = script.get("vars", {})
        
        # Provide guidance for each variable type
        var_guidance = {}
        for var_name, var_type in vars_dict.items():
            guidance = {
                "type": var_type,
                "required": True,  # Assume all are required unless script says otherwise
            }
            
            # Add specific guidance based on type
            if var_type == "ObjectVar":
                # Suggest which tool to use to find the object ID
                if "tenant" in var_name.lower():
                    guidance["help"] = "Use search_objects('dcim/tenants', 'query') to find tenant ID"
                    guidance["example"] = "Search for tenant name and use the 'id' field"
                elif "region" in var_name.lower():
                    guidance["help"] = "Use search_objects('dcim/regions', 'query') to find region ID"
                    guidance["example"] = "Search for region name and use the 'id' field"
                elif "site" in var_name.lower():
                    guidance["help"] = "Use get_sites() or search_objects('dcim/sites', 'query') to find site ID"
                    guidance["example"] = "Search for site name and use the 'id' field"
                elif "device" in var_name.lower():
                    guidance["help"] = "Use get_devices() or search_objects('dcim/devices', 'query') to find device ID"
                    guidance["example"] = "Search for device name and use the 'id' field"
                else:
                    guidance["help"] = f"Use search_objects() to find the {var_name} object ID"
                    guidance["example"] = "Search by name and use the 'id' field from results"
            elif var_type == "StringVar":
                guidance["help"] = "Provide as a string value"
                guidance["example"] = f'"example_{var_name}"'
            elif var_type == "IntegerVar":
                guidance["help"] = "Provide as an integer value"
                guidance["example"] = "10"
            elif var_type == "BooleanVar":
                guidance["help"] = "Provide as true or false"
                guidance["example"] = "true"
            else:
                guidance["help"] = f"Provide value for {var_type}"
                guidance["example"] = "See NetBox documentation"
            
            var_guidance[var_name] = guidance
        
        return {
            "success": True,
            "script_id": script_id,
            "script_name": script.get("name"),
            "description": script.get("description"),
            "variables": var_guidance
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def search_for_object_id(endpoint: str, search_name: str, name_field: str = "name") -> Dict[str, Any]:
    """
    Search for NetBox objects by name and return their IDs.
    
    This is a helper tool for finding object IDs needed for ObjectVar parameters
    in custom scripts. It searches for objects and returns their IDs.
    
    Args:
        endpoint: NetBox API endpoint (e.g., "dcim/tenants", "dcim/regions", "dcim/sites")
        search_name: The name to search for
        name_field: Field name to search in (default: "name")
    
    Returns:
        Dict with matching objects and their IDs
    
    Example:
        # Find tenant ID for "Acme Corp"
        result = search_for_object_id("dcim/tenants", "Acme Corp")
        tenant_id = result["matches"][0]["id"]
        
        # Find region ID for "Europe"
        result = search_for_object_id("dcim/regions", "Europe")
        region_id = result["matches"][0]["id"]
        
        # Find site ID
        result = search_for_object_id("dcim/sites", "DC-East-01")
        site_id = result["matches"][0]["id"]
    """
    try:
        # Search using the 'q' parameter for text search
        params = {"q": search_name, "limit": 10}
        results = client.get(endpoint, params=params)
        
        # Handle both list and dict responses
        if isinstance(results, list):
            matches = results
        elif isinstance(results, dict) and 'results' in results:
            matches = results['results']
        else:
            matches = []
        
        # Extract relevant fields for easier use
        simplified_matches = []
        for match in matches:
            simplified = {
                "id": match.get("id"),
                "name": match.get("name") or match.get("display"),
                "display": match.get("display"),
                "url": match.get("url")
            }
            simplified_matches.append(simplified)
        
        return {
            "success": True,
            "endpoint": endpoint,
            "search_name": search_name,
            "count": len(simplified_matches),
            "matches": simplified_matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def find_custom_script(query: str) -> Dict[str, Any]:
    """
    Search for custom scripts by name or description.
    
    This tool helps find the right script when you have a natural language description
    of what you want to do. It searches script names and descriptions for matches.
    
    Args:
        query: Search term (e.g., "create site", "add switches", "provision")
    
    Returns:
        Dict with matching scripts and their details
    
    Example:
        # Find scripts related to creating sites
        matches = find_custom_script("create site")
        
        # Result might include:
        # - CreateSiteAndLocations: "Script to create a new site and associated floors"
        # - ProvisionNewSite: "Provision a complete site with VLANs and IP space"
    """
    try:
        # Get all scripts
        all_scripts_result = get_custom_scripts()
        
        if not all_scripts_result.get("success"):
            return all_scripts_result
        
        all_scripts = all_scripts_result.get("data", [])
        query_lower = query.lower()
        
        # Search in name and description
        matches = []
        for script in all_scripts:
            name = script.get("name", "").lower()
            description = script.get("description", "").lower()
            display = script.get("display", "").lower()
            
            # Calculate relevance score
            relevance = 0
            if query_lower in name:
                relevance += 10
            if query_lower in description:
                relevance += 5
            if query_lower in display:
                relevance += 3
            
            # Also check for word matches
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    if word in name:
                        relevance += 2
                    if word in description:
                        relevance += 1
            
            if relevance > 0:
                matches.append({
                    **script,
                    "relevance": relevance
                })
        
        # Sort by relevance
        matches.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Remove relevance score from output (internal use only)
        for match in matches:
            match.pop("relevance", None)
        
        return {
            "success": True,
            "query": query,
            "count": len(matches),
            "matches": matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def execute_custom_script(script_id: int, data: Optional[Dict[str, Any]] = None, commit: bool = True) -> Dict[str, Any]:
    """
    Execute a NetBox custom script by ID.
    
    Custom scripts are Python-based workflows that can perform complex operations
    like creating sites with all necessary components, bulk device provisioning,
    IP address allocation workflows, or compliance automation.
    
    IMPORTANT - ObjectVar Parameters:
    - Scripts with ObjectVar parameters (like "tenant", "region", "site") require object IDs, not names
    - Use get_script_variables(script_id) to see what parameters are needed
    - Use search_for_object_id(endpoint, name) to find object IDs by name
    
    Workflow:
    1. get_custom_scripts() - Find the script you want
    2. get_script_variables(script_id) - See what parameters it needs
    3. search_for_object_id() - Look up any object IDs needed
    4. execute_custom_script() - Run with all parameters
    5. get_script_job_status() - Check if it completed
    
    Args:
        script_id: Script ID from get_custom_scripts() (e.g., 17 for "CreateSiteAndLocations")
        data: Dictionary of parameters required by the script (must match script's "vars")
              - ObjectVar: Provide object ID (integer) - use search_for_object_id() to find
              - StringVar: Provide string value
              - IntegerVar: Provide integer value
              - BooleanVar: Provide true/false
        commit: Whether to commit changes (default: True, use False for dry-run)
    
    Returns:
        Dict with success status and job information for tracking execution
    
    Example - Complete workflow:
        # Step 1: Find tenant ID (ObjectVar)
        tenant_result = search_for_object_id("dcim/tenants", "Acme Corp")
        tenant_id = tenant_result["matches"][0]["id"]  # e.g., 1
        
        # Step 2: Find region ID (ObjectVar)
        region_result = search_for_object_id("dcim/regions", "Europe")
        region_id = region_result["matches"][0]["id"]  # e.g., 2
        
        # Step 3: Execute the script with IDs
        result = execute_custom_script(
            script_id=17,  # CreateSiteAndLocations
            data={
                "tenant": tenant_id,      # ObjectVar: Use ID, not name!
                "region": region_id,      # ObjectVar: Use ID, not name!
                "site_name": "DC-East-01", # StringVar: Use string
                "address": "123 Main St",  # StringVar: Use string
                "number_of_floors": 3,     # IntegerVar: Use integer
                "lowest_floor": 0          # IntegerVar: Use integer
            },
            commit=True
        )
        
        # Step 4: Check execution status
        job_id = result["job_id"]
        status = get_script_job_status(job_id)
    """
    try:
        # Build the script execution payload
        payload = {
            "data": data or {},
            "commit": commit
        }
        
        # Execute the script via POST to extras/scripts/{id}/
        result = client.create(f"extras/scripts/{script_id}", payload)
        
        # Extract job information from response
        job_info = None
        job_id = None
        
        if isinstance(result, dict):
            if "job" in result:
                job_info = result["job"]
                job_id = job_info.get("id") if isinstance(job_info, dict) else None
            elif "id" in result:
                # Sometimes the job info is at the top level
                job_id = result.get("id")
        
        return {
            "success": True,
            "message": "Script execution started successfully",
            "script_id": script_id,
            "job_id": job_id,
            "job_info": job_info,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to execute script {script_id}. Check that script ID is valid and all required parameters are provided."
        }

@mcp.tool()
def get_script_job_status(job_id: int) -> Dict[str, Any]:
    """
    Get the status and results of a custom script execution job.
    
    After executing a custom script, use this to check if it completed successfully,
    retrieve output logs, and see any errors that occurred.
    
    Args:
        job_id: The job ID returned from execute_custom_script()
    
    Returns:
        Dict with job status, completion state, logs, and results
    
    Example:
        # Check if script completed
        status = get_script_job_status(job_id=42)
        print(status["data"]["status"])  # completed, pending, running, failed
    """
    try:
        job = client.get("core/jobs", id=job_id)
        return {
            "success": True,
            "data": job,
            "status": job.get("status", {}).get("value") if isinstance(job, dict) else None,
            "completed": job.get("completed") if isinstance(job, dict) else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_script_jobs(limit: int = 50, script_name: Optional[str] = None) -> Dict[str, Any]:
    """
    List recent custom script execution jobs.
    
    View history of script executions, their status, and when they ran.
    Useful for tracking automation workflows and troubleshooting failures.
    
    Args:
        limit: Maximum number of jobs to return (default: 50)
        script_name: Optional filter by specific script name
    
    Returns:
        Dict with list of recent script execution jobs
    """
    try:
        params = {"limit": limit, "object_type": "extras.script"}
        if script_name:
            params["name"] = script_name
        
        jobs = client.get("core/jobs", params=params)
        return {"success": True, "data": jobs}
    except Exception as e:
        return {"success": False, "error": str(e)}

# MCP server instance was created early in the file with decorators handling tool registration

# ---- Server Startup ----
if __name__ == "__main__":
    print(f"🚀 NetBox MCP Server starting...")
    print(f"🔗 NetBox URL: {netbox_url}")
    print(f"🛠️  Available tools: 21 (DCIM, IPAM, Custom Scripts, CRUD operations)")
    print(f"🌐 Server starting on: http://{mcp_host}:{mcp_port}")
    print(f"🔗 HTTP endpoint: http://{mcp_host}:{mcp_port}")
    print(f"✅ Server ready for MCP client connections via HTTP.")
    print(f"")
    print(f"📋 Available NetBox operations:")
    print(f"   🏢 DCIM: Sites, Devices, Device Types")
    print(f"   🌐 IPAM: IP Addresses, Prefixes, VLANs")
    print(f"   🔍 Search & Query: Universal search across objects")
    print(f"   ✏️  CRUD: Create, Read, Update, Delete operations")
    print(f"   🔧 Custom Scripts: AI-driven workflow execution with ObjectVar resolution")
    
    # Start the MCP server in HTTP mode
    try:
        mcp.run(transport="http", host=mcp_host, port=mcp_port)
    except Exception as e:
        print(f"❌ Failed to start HTTP server: {e}")
        print(f"💡 Trying alternative HTTP startup method...")
        # Alternative method if the above doesn't work
        import uvicorn
        app = mcp.create_app()
        uvicorn.run(app, host=mcp_host, port=mcp_port, log_level="info")
