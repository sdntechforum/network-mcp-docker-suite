# NetBox MCP Server

A Model Context Protocol (MCP) server that provides comprehensive access to NetBox DCIM/IPAM capabilities for infrastructure documentation, IP address management, and device lifecycle tracking with enterprise-grade security.

## Overview

This MCP server provides **complete** API-based access to NetBox capabilities, enabling:

- **DCIM (Data Center Infrastructure Management)**: Complete facility, rack, and device management
- **IPAM (IP Address Management)**: IP address spaces, prefixes, and VLAN management
- **Custom Scripts & Workflows**: Execute complex automation workflows via natural language 🆕
- **Device Lifecycle Management**: Hardware inventory, device types, and lifecycle tracking
- **Network Documentation**: Comprehensive network topology and connection documentation
- **Cable Management**: Physical and logical connection tracking
- **Custom Fields**: Extensible data model with custom attributes
- **Multi-Tenancy**: Organization and tenant-based resource separation
- **HTTP Transport**: Modern MCP transport for MCP clients (Cursor, LibreChat, etc.)

### 🆕 Custom Scripts Support

This server now supports **NetBox Custom Scripts**, enabling:
- ✅ **Natural Language Workflow Execution**: "Run workflow to create a new site"
- ✅ **Script Discovery**: AI automatically finds the right script based on descriptions
- ✅ **Complex Automation**: Site provisioning, device onboarding, IP allocation workflows
- ✅ **Job Tracking**: Monitor script execution status and retrieve results

## Features

### Available Tools

**Site & Location Management:**
- **`get_sites`**: List and manage data center sites and locations
- **`get_site_by_id`**: Get detailed information about specific sites
- **`create_site`**: Create new data center sites
- **`get_racks`**: List equipment racks and their configurations

**Device & Hardware Management:**
- **`get_devices`**: List network and compute devices
- **`get_device_by_id`**: Get detailed device information and specifications
- **`create_device`**: Add new devices to inventory
- **`get_device_types`**: List available device types and models
- **`get_manufacturers`**: List equipment manufacturers

**IP Address Management (IPAM):**
- **`get_ip_addresses`**: List and manage IP address assignments
- **`create_ip_address`**: Assign new IP addresses to devices/interfaces
- **`get_prefixes`**: List network prefixes and subnets
- **`get_vlans`**: List VLAN configurations and assignments
- **`get_vrfs`**: List Virtual Routing and Forwarding instances

**Network Topology:**
- **`get_interfaces`**: List device network interfaces
- **`get_cables`**: List physical cable connections
- **`get_connections`**: List logical network connections
- **`get_circuits`**: List WAN circuits and provider connections

**Custom Scripts & Automation:**
- **`get_custom_scripts`**: List all available custom scripts and workflows
- **`find_custom_script`**: Search for scripts by natural language description
- **`get_script_variables`**: Get detailed info about script parameters (especially ObjectVars)
- **`get_object_choices`**: List all available options for ObjectVar parameters (recommended)
- **`search_for_object_id`**: Look up object IDs by name (deprecated - use get_object_choices instead)
- **`execute_custom_script`**: Run custom scripts with parameters
- **`get_script_job_status`**: Check script execution status and results
- **`list_script_jobs`**: View history of script executions

**Documentation & Reporting:**
- **`search_objects`**: Universal search across all NetBox objects
- **`get_custom_fields`**: List custom field definitions
- **`update_object`**: Update existing NetBox objects
- **`delete_object`**: Remove objects from NetBox inventory

### Security Features

- 🔐 **Token-Based Authentication** - NetBox API token loaded from environment variables
- 🔐 **Read-Only Operations** - Safe operations with configurable write access
- 🔐 **SSL/HTTPS Support** - Secure communication with NetBox instance
- 🔐 **Input Validation** - Parameter validation for all API calls
- 🔐 **Rate Limiting** - Respects NetBox API rate limits

## Configuration

### Environment Variables

Create a `.env` file in the `netbox-mcp-server/` directory:

```bash
# Copy the environment template
cp .env.example .env
```

**Required Configuration:**
```bash
# NetBox API Configuration (Required)
NETBOX_URL=https://netbox.example.com        # Your NetBox instance URL
NETBOX_TOKEN=your_netbox_token_here          # NetBox API token with appropriate permissions

# MCP Server Configuration (Optional)
MCP_HOST=localhost                           # Host for MCP server (default: localhost)
MCP_PORT=8001                               # Port for MCP server (default: 8001)
```

### Getting NetBox API Token

1. **Login** to NetBox web interface
2. **Navigate** to your Profile (top right) → API Tokens
3. **Create** new token with appropriate permissions:
   - **Read**: For monitoring and documentation
   - **Write**: For device provisioning and updates  
   - **Delete**: For cleanup operations (use carefully)
4. **Copy** the token to your `.env` file

### Environment Variable Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NETBOX_URL` | NetBox instance URL (include https://) | - | ✅ Yes |
| `NETBOX_TOKEN` | NetBox API token | - | ✅ Yes |
| `MCP_HOST` | Host for MCP server | `localhost` | No |
| `MCP_PORT` | Port for MCP server | `8001` | No |

### NetBox API Token

1. **Login to NetBox** web interface
2. **Navigate to** Profile → API Tokens
3. **Create Token** with appropriate permissions:
   - **Read**: For monitoring and documentation
   - **Write**: For device provisioning and updates
   - **Delete**: For cleanup operations (use carefully)

## Custom Scripts & Workflow Automation

The NetBox MCP Server supports **NetBox Custom Scripts**, enabling you to execute complex workflows through natural language prompts.

### How It Works

1. **NetBox Custom Scripts** are Python-based workflows stored in NetBox (`/opt/netbox/scripts/`)
2. Each script has a **name**, **description**, and **required variables (vars)**
3. Variables can be:
   - **ObjectVar**: Requires object ID (e.g., tenant_id, region_id, site_id)
   - **StringVar**: Requires text string
   - **IntegerVar**: Requires integer number
   - **BooleanVar**: Requires true/false
4. You can ask the AI to run workflows in natural language
5. The AI automatically resolves ObjectVars by searching for objects and their IDs

### Example Workflow

**User**: "Run workflow to create a new site called DC-East-01"

**AI Process (Improved UX)**:
1. Calls `find_custom_script("create site")` to discover matching workflows
2. Finds `CreateSiteAndLocations` (ID 17)
3. Calls `get_script_variables(17)` to see it needs:
   - `tenant` (ObjectVar) - needs tenant ID
   - `region` (ObjectVar) - needs region ID
   - `site_name` (StringVar) - "DC-East-01"
   - `number_of_floors` (IntegerVar) - asks user
4. **IMPROVED**: Calls `get_object_choices("dcim/tenants")` to show ALL tenants:
   - Shows: "1: Acme Corp, 2: TechCo, 3: GlobalNet"
   - User picks: "Acme Corp" → uses ID 1
5. **IMPROVED**: Calls `get_object_choices("dcim/regions")` to show ALL regions:
   - Shows: "1: North America, 2: Europe, 3: Asia Pacific"
   - User picks: "Europe" → uses ID 2
6. Executes `execute_custom_script()` with all resolved parameters
7. Monitors execution with `get_script_job_status()`
8. Reports results back to user

**Benefits**:
- ✅ No typos - user picks from list
- ✅ No failed searches - always valid options
- ✅ Better UX - clear choices
- ✅ Faster - no guessing

### Common Use Cases

**Site Provisioning Workflows:**
- Create site with VLANs, prefixes, and device racks
- Configure standard site topology
- Set up management networks and IP addressing

**Device Onboarding:**
- Bulk device provisioning with standard configurations
- IP address allocation for new devices
- Cable and connection documentation

**IP Management Workflows:**
- Allocate IP blocks for new sites
- Reserve IP ranges for specific purposes
- Validate IP addressing schemes

**Compliance & Auditing:**
- Run compliance checks across infrastructure
- Generate audit reports
- Validate configurations against standards

### Script Discovery

The AI can intelligently match your natural language requests to scripts using `find_custom_script()`:

| Your Request | Matched Script | Script ID |
|--------------|----------------|-----------|
| "Create a new site with floors" | `CreateSiteAndLocations` | 17 |
| "Add switches to site" | `AddSwitchesToSite` | 18 |
| "Create IP addresses" | `CreateIps` | 16 |

**Example workflow:**
```python
# User: "Run workflow to create a new site"
# AI process:
matches = find_custom_script("create site")
# Returns: CreateSiteAndLocations (ID 17)

# AI then executes with user-provided parameters
result = execute_custom_script(
    script_id=17,
    data={"site_name": "DC-East-01", ...}
)
```

### Requirements

**NetBox Configuration:**
1. Custom scripts must be installed in NetBox (`/opt/netbox/scripts/`)
2. Scripts must be properly registered and available via the API
3. API token must have permissions to execute scripts

**Script Best Practices:**
- Add clear descriptions to scripts for AI discovery
- Use descriptive parameter names
- Include validation and error handling
- Document expected inputs and outputs

## Usage Examples

### Site Management

```python
# List all data center sites
sites = get_sites()

# Get specific site details
site_detail = get_site_by_id(site_id=1)

# Create new data center site
new_site = create_site(
    name="DC-East-01", 
    slug="dc-east-01",
    status="active"
)
```

### Device Management

```python
# List all devices
devices = get_devices()

# Filter devices by site
devices_by_site = get_devices(site_id=1)

# Get specific device details
device_detail = get_device_by_id(device_id=123)

# Add new device to inventory
new_device = create_device(
    name="core-switch-01",
    device_type_id=5,
    site_id=1,
    status="active"
)
```

### IP Address Management

```python
# List IP address assignments
ip_addresses = get_ip_addresses()

# Filter by VRF
vrf_ips = get_ip_addresses(vrf_id=2)

# Assign new IP address
new_ip = create_ip_address(
    address="192.168.1.10/24",
    status="active",
    description="Core switch management"
)

# List network prefixes
prefixes = get_prefixes()

# List VLANs
vlans = get_vlans(site_id=1)
```

### Search & Documentation

```python
# Universal search across NetBox
search_results = search_objects(
    endpoint="devices",
    query="cisco"
)

# List available device types
device_types = get_device_types()

# Get manufacturer information
manufacturers = get_manufacturers()
```

### Custom Scripts & Workflows

```python
# COMPLETE WORKFLOW: Improved UX with object selection

# Step 1: Find the script you want to run
matches = find_custom_script("create site")
script_id = matches["matches"][0]["id"]  # e.g., 17

# Step 2: Get detailed information about required parameters
vars_info = get_script_variables(script_id=17)
print(vars_info["variables"])
# Shows:
#   tenant (ObjectVar) - needs tenant ID
#   region (ObjectVar) - needs region ID
#   site_name (StringVar) - provide as string
#   number_of_floors (IntegerVar) - provide as integer

# Step 3: Show available choices for ObjectVar parameters
# IMPROVED: Show user ALL available tenants to choose from
tenants = get_object_choices("dcim/tenants")
print("Available tenants:")
for t in tenants["choices"]:
    print(f"  {t['id']}: {t['name']}")
# Output:
#   1: Acme Corp
#   2: TechCo
#   3: GlobalNet

# User selects: "Acme Corp"
tenant_id = 1  # Selected from list above

# IMPROVED: Show user ALL available regions to choose from
regions = get_object_choices("dcim/regions")
print("Available regions:")
for r in regions["choices"]:
    print(f"  {r['id']}: {r['name']}")
# Output:
#   1: North America
#   2: Europe
#   3: Asia Pacific

# User selects: "Europe"
region_id = 2  # Selected from list above

# Step 4: Execute the script with all parameters
job_result = execute_custom_script(
    script_id=17,
    data={
        "tenant": tenant_id,             # ObjectVar: ID from choice list
        "region": region_id,             # ObjectVar: ID from choice list
        "site_name": "DC-West-01",       # StringVar: String
        "address": "123 Data Center Dr",  # StringVar: String
        "number_of_floors": 3,           # IntegerVar: Integer
        "lowest_floor": 0                # IntegerVar: Integer
    },
    commit=True
)

# Step 5: Monitor execution status
if job_result["success"]:
    job_id = job_result["job_id"]
    status = get_script_job_status(job_id=job_id)
    
    print(f"Status: {status['status']}")  # completed, pending, running, failed
    print(f"Completed: {status['completed']}")

# View recent script executions
recent_jobs = list_script_jobs(limit=10)
```

## Docker Deployment

### Build and Run

```bash
# Build the container
docker build -t netbox-mcp-server .

# Run with environment file
docker run -d --name netbox-mcp-server \
  --env-file .env \
  -p 8001:8001 \
  netbox-mcp-server
```

### Docker Compose

Add to your `docker-compose.yml` file:

```yaml
services:
  netbox-mcp-server:
    build: ./netbox-mcp-server
    container_name: netbox-mcp-server
    env_file:
      - ./netbox-mcp-server/.env
    environment:
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8001
    ports:
      - "8001:8001"
    restart: unless-stopped
    networks:
      - default
```

**Or use the main project's deployment:**
```bash
# From project root
./deploy.sh start netbox        # Deploy only NetBox server
./deploy.sh start docs          # Deploy NetBox + Catalyst Center
./deploy.sh start all           # Deploy all servers including NetBox
```

### Logs and Debugging

```bash
# View container logs
docker logs netbox-mcp-server

# Enable debug logging
docker run -e LOG_LEVEL=DEBUG netbox-mcp-server
```

## Integration

### MCP Client Configuration

**Cursor IDE (`~/.cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "NetBox-MCP-Server": {
      "transport": "http",
      "url": "http://localhost:8001/mcp",
      "timeout": 60000
    }
  }
}
```

**LibreChat (`librechat.yaml`):**
```yaml
mcpServers:
  Netbox-MCP-Server:
    type: streamable-http
    url: http://netbox-mcp-server:8001/mcp
    timeout: 60000
```

## Common Use Cases

### Infrastructure Documentation

- **Asset Inventory**: Track all network devices, servers, and infrastructure
- **Cable Management**: Document physical connections and cable runs
- **IP Address Management**: Maintain accurate IP address assignments
- **Network Topology**: Visualize and document network architecture

### Capacity Planning

- **Rack Space**: Monitor rack utilization and plan expansions
- **IP Space**: Track IP address utilization and plan subnets
- **Power & Cooling**: Document power and cooling requirements
- **Growth Planning**: Historical data for infrastructure growth

### Compliance & Auditing

- **Asset Tracking**: Maintain accurate hardware inventory
- **Change Management**: Track infrastructure changes over time
- **Documentation**: Ensure network documentation is current
- **Reporting**: Generate compliance and audit reports

### Network Automation

- **Device Provisioning**: Automate device onboarding
- **IP Assignment**: Automated IP address management
- **Configuration Management**: Integration with automation tools
- **Monitoring Integration**: Feed data to monitoring systems

## Troubleshooting

### Common Issues

**Container Won't Start:**
```bash
# Check logs for errors
docker logs netbox-mcp-server

# Common causes:
# 1. Missing NETBOX_URL or NETBOX_TOKEN in .env file
# 2. Port 8001 already in use (check: lsof -i :8001)
# 3. Invalid NetBox URL format (must include https://)
```

**Connection Errors:**
```bash
# Test NetBox connectivity
curl -H "Authorization: Token YOUR_TOKEN" \
  "https://netbox.example.com/api/"

# Expected response: NetBox API information
# Error response: Connection timeout/refused or 401 Unauthorized
```

**Authentication Issues:**
```bash
# Verify API token permissions
curl -H "Authorization: Token YOUR_TOKEN" \
  "https://netbox.example.com/api/users/me/"

# Check token has required permissions (read/write/delete)
curl -H "Authorization: Token YOUR_TOKEN" \
  "https://netbox.example.com/api/users/tokens/"
```

**MCP Client Connection Issues:**
```bash
# Verify MCP endpoint is accessible
curl http://localhost:8001/mcp

# Should return MCP protocol response
# If connection refused, check container status:
docker ps | grep netbox-mcp-server
```

**SSL Certificate Issues:**
```bash
# Test SSL connectivity
openssl s_client -connect netbox.example.com:443 -servername netbox.example.com

# For self-signed certificates, you may need to configure trust
# Check container logs for SSL verification errors
```

### Performance Optimization

- **Pagination**: Use appropriate page sizes for large datasets
- **Filtering**: Apply filters to reduce data transfer
- **Caching**: Results cached appropriately to reduce API calls
- **Indexing**: Ensure NetBox database is properly indexed

## API Reference

This server provides access to **NetBox REST API v2.8+** including:

- **DCIM**: Sites, racks, devices, device types, manufacturers
- **IPAM**: IP addresses, prefixes, VRFs, VLANs, aggregates  
- **Circuits**: Providers, circuit types, circuits
- **Extras**: Custom fields, tags, webhooks
- **Tenancy**: Tenants, tenant groups
- **Users**: User accounts, groups, permissions

For complete API documentation, see: [NetBox REST API Documentation](https://netbox.readthedocs.io/en/stable/rest-api/)

## Security Considerations

### Production Deployment

1. **API Token Security**: Store NetBox tokens in secure secrets management
2. **Network Security**: Use HTTPS and restrict network access
3. **Access Control**: Configure appropriate NetBox user permissions
4. **Monitoring**: Monitor API usage and access patterns
5. **Backup**: Regular backup of NetBox database and configuration

### Best Practices

- **Token Rotation**: Regularly rotate NetBox API tokens
- **Least Privilege**: Grant minimum required permissions
- **Audit Logging**: Enable NetBox audit logging
- **SSL/TLS**: Use strong SSL/TLS configuration
- **Network Segmentation**: Isolate NetBox on management network

## Support

For issues and questions:

1. **Check Logs**: `docker logs netbox-mcp-server`
2. **Verify Token**: Test with NetBox API directly  
3. **Network Connectivity**: Ensure access to NetBox instance
4. **Permissions**: Verify API token has required permissions

## Contributing

This MCP server is part of the [Network MCP Docker Suite](../README.md). Contributions welcome!

## License

Licensed under the Cisco Sample Code License, Version 1.1. See [LICENSE](../LICENSE) for details.
