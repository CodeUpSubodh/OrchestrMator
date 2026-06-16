# System Architecture and Data Flow

## High-Level Architecture

```
Frontend (XML Request)
         ↓
Request Handler (request_handler.py)
         ↓
Input Handler Loader → Input Handler (processes Excel/input)
         ↓
Change Handler (change_handler.py)
         ↓
Node Handler (node_handler.py) [parallel/sequential/batch]
         ↓
SSH Client → Network Nodes (OSS/NE)
         ↓
Command Builder (builds commands with variables)
         ↓
Parser Logic (extract data from outputs)
         ↓
State_Data_Map (stores intermediate results)
         ↓
Additional Module (post-processing)
         ↓
Result Storage (Database + Excel/CSV Reports)
         ↓
Email Notifications
```

## Request Flow (Step-by-Step)

### 1. Request Initiation
- Frontend sends XML request with:
  - `CR_ID` (Change Request ID)
  - `ACTIVITY_ID` and `ACTIVITY_NAME`
  - `DOMAIN_ID` and `DOMAIN_NAME` (ran, core, pcn, pbn, paco, txn, core2)
  - `NODE_USER`, `NODE_PASS` (credentials)
  - `INPUT_TYPE` (1=direct XML, 2=Excel upload, 3=pre-uploaded file)
  - Input data or file reference

### 2. Request Handler Processing
- Parses XML to dictionary
- Determines INPUT_TYPE
- If INPUT_TYPE=2 or 3, loads appropriate Input Handler
- Triggers `input_handler_loader.detect_input_handlers()` 
- Calls `run_preprocessor()` on detected handler

### 3. Input Handler Execution
- Reads input Excel sheet (e.g., node list with IPs, parameters)
- Creates `node_pars` dictionary for each node
- Structure example:
  ```python
  node_pars["NODE001"] = [{
      'node_ip': '10.20.30.40',
      'node_name': 'NODE001',
      'node_user': 'admin',
      'node_pass': 'encrypted_pass',
      'syslog_ip': '192.168.1.100',
      'output_sheet_file': '/path/to/output.xlsx',
      'exception_sheet': '/path/to/exception.csv',
      'cr_id': '12345',
      'DYNAMIC_PARS': {}  # Populated during execution
  }]
  ```
- Adds `custom_reporting_module_data` for Additional Module configuration
- Returns updated `input_data_map` with `node_details_map`

### 4. Change Handler Initialization

- Receives `request_data` with all node information
- Fetches Activity Configuration from database
- Sorts nodes into execution modes:
  - **Sequential**: Nodes executed one after another
  - **Parallel**: Nodes executed concurrently (max 50)
  - **Batch**: Controlled parallel execution in batches
- Spawns Node Handler instances per node

### 5. Node Handler Execution (Per Node)
- Establishes SSH connection to OSS or directly to node
- Fetches command sequence from database using `CHANGE_SEQUENCE_ID`
- Iterates through commands in sequence
- For each command:
  a. **Build Command**: Replace `<<<keywords>>>` with values from node_pars or DYNAMIC_PARS
  b. **Execute Command**: Send via SSH, wait for prompt match
  c. **Parse Output**: Apply parser logic defined in Activity Configuration
  d. **Update State**: Store extracted values in State_Data_Map/DYNAMIC_PARS
  e. **Write Log**: Record command output to log file
  f. **Write Output**: Update Output Excel sheet if configured
- Handles errors, retries, timeouts
- Writes final connectivity status to CSV

### 6. Parser Logic Application
- Parser class name defined in Activity Configuration column "Field - 3"
- Example: `{"parse": {"pbn": ["ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_ADC"]}}`
- Parser loaded dynamically via `logic_loader.detect_logic_handlers()`
- Parser's `apply(command_output)` method called
- Returns extracted data in `token_map` and return code
- On success (rcode=0), token_map values merged into State_Data_Map

### 7. Additional Module Execution
- After all nodes complete, Change Handler triggers Additional Module
- Module name specified in Input Handler's `custom_reporting_module_data`
- Common modules:
  - `merge_csv_to_excel.py`: Combines CSV files into Excel workbook
  - Email notification modules
  - CSV merger and conclusion calculators
  - Custom report formatting

### 8. Final Report Generation
- Change Handler aggregates all node reports
- Writes to database `change_report` table
- Summary includes success/fail counts
- CSV/Excel files archived
- Email sent to stakeholders
