# Input Handler - Deep Dive

## Purpose
Input Handler processes the input Excel sheet and converts it into `node_pars` dictionary structure that Node Handler uses for execution.

## File Location
- `lib/ace/input_handlers/{domain}/{ACTIVITY_NAME}_INPUT_HANDLER.py`
- Example: `REFERENCE/INPUT_HANDLER/ACE_MPBN_NOKIA_SYSLOG_PRECHECK_INPUT_HANDLER.py`
- Organized by domain: ran, core, pcn, pbn, paco, txn, core2

## Class Structure

```python
class {ACTIVITY_NAME}_INPUT_HANDLER:
    def __init__(self, input_data_map, logger_name=None)
    def extract_values(self)  # Property
    def child_extract_values(self, input_sheet)
    def update_input_map(self)
    def run_preprocessor(self)  # Entry point
```

## Input Handler Workflow

### 1. Initialization
- Receives `input_data_map` from Request Handler
- Contains:
  - `instance_id`, `app_user`, `cr_id`
  - `domain_id`, `domain_name`, `activity_id`, `activity_name`
  - `node_user`, `node_pass` (credentials)
  - `input_type` (2=Excel upload, 3=pre-uploaded)
  - `input_file` or `pre_uploaded_file` path
  - `change_config_map` (activity configuration)

### 2. Extract Input Sheet Data
```python
def extract_input_sheet_data(self, excel_file):
    df = pd.read_excel(excel_file, sheet_name=0)
    df = self.clean_df(df)  # Remove empty rows, fill NaN
    return df
```

### 3. Build node_pars Dictionary
For each row in input Excel:
```python
for index, row in df.iterrows():
    node_name = row.get("Node Name", "").strip()
    node_ip = row.get("Node IP", "").strip()
    
    node_dict = {
        'node_ip': node_ip,
        'node_name': node_name,
        'node_user': self.node_user,
        'node_pass': self.node_pass,
        'syslog_ip': row.get("Syslog IP", ""),
        'output_sheet_file': '/path/to/output.xlsx',
        'connectivity_csv_file': '/path/to/connectivity.csv',
        'exception_sheet': '/path/to/exception.csv',
        'cr_id': self.cr_id,
        'Decrypt_required': 'no',
        'jump_host_ip': app.FE_HOST,  # OSS IP for SSH tunneling
        'jump_host_user': app.FE_USER,
        'jump_host_pass': app.FE_PASS,
    }
    
    node_pars[node_name] = [node_dict]
```

### 4. Create Output Files

```python
archive_path = os.path.join(app.ARCHIVE_PATH, str(self.cr_id))
activity_path = os.path.join(archive_path, "activity")
report_path = os.path.join(archive_path, "reports")

# CSV files for intermediate data
connectivity_csv = os.path.join(report_path, f"{self.cr_id}_CONNECTIVITY.csv")
exception_sheet = os.path.join(report_path, f"{self.cr_id}_EXCEPTION.csv")

# Final output Excel
output_excel = os.path.join(report_path, f"{self.cr_id}_OUTPUT.xlsx")

# Initialize with headers
self.write_csv_headers(connectivity_csv, ["Node Name", "Status", "Remark"])
self.write_excel_headers(output_excel, ["Node Name", "Node IP", "Syslog IP", ...])
```

### 5. Add Additional Module Configuration
```python
additional_module_data = {
    'custom_reporting_class_name': 'MergeCSVtoExcel',
    'custom_reporting_module_name': 'merge_csv_to_excel',
    'additional_reporting_data': {
        'report_file_excel': '/path/to/final_report.xlsx',
        'sheet_name_to_csv_mapping': [
            ('Connectivity', '/path/to/connectivity.csv'),
            ('Exception', '/path/to/exception.csv')
        ]
    }
}

# Add to all nodes or specific nodes
self.add_additional_module(node_pars, additional_module_data, apply_to_all=True)
```

### 6. Return Updated Input Map
```python
self.input_data_map["node_details_map"] = node_pars
return self.input_data_map
```

## Input Excel Sheet Format

Typical columns:
- **Node Name**: Identifier (e.g., NODE001)
- **Node IP**: Management IP address
- **Node Type**: Router, BSC, MME, etc.
- **Syslog IP**: For log collection
- **Circle**: Geographic region
- **OSS IP**: Operation Support System IP
- Additional columns specific to activity

## node_pars Dictionary Structure

```python
node_pars = {
    "NODE001": [{
        'connectivity_csv_file': '/archive/12345/reports/12345_CONNECTIVITY.csv',
        'exception_msg': '',
        'exception_sheet': '/archive/12345/reports/12345_EXCEPTION.csv',
        'node_ip': '10.20.30.40',
        'node_name': 'NODE001',
        'node_type': 'ROUTER',
        'node_user': 'admin',
        'node_pass': 'encrypted_pass',
        'syslog_ip': '192.168.1.100',
        'output_sheet_file': '/archive/12345/reports/12345_OUTPUT.xlsx',
        'cr_id': '12345',
        'Decrypt_required': 'no',
        'jump_host_ip': '10.50.60.70',
        'jump_host_user': 'ossuser',
        'jump_host_pass': 'osspass',
        'DYNAMIC_PARS': {}  # Populated during execution
    }]
}
```

## Dynamic Parameters (DYNAMIC_PARS)

Added during Node Handler execution:
```python
node_pars["DYNAMIC_PARS"]["ITEM_INDEX"] = 0
node_pars["DYNAMIC_PARS"]["CURRENT_UTC_TIME"] = "2025-01-15T10:30:00"
node_pars["DYNAMIC_PARS"]["DATE"] = "20250115"
node_pars["DYNAMIC_PARS"]["CR_ID"] = "12345"
node_pars["DYNAMIC_PARS"]["NODE_IP"] = "10.20.30.40"
# Parser adds extracted values:
node_pars["DYNAMIC_PARS"]["syslog_id"] = "100"
node_pars["DYNAMIC_PARS"]["log_id"] = "5"
```
