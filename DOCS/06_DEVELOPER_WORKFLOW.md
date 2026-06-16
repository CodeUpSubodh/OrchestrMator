# Developer Workflow - How to Create an Automation

## Overview
Creating a new automation requires a developer to manually create 5-6 independent files and test them on the server. The process is error-prone and time-consuming.

## Step-by-Step Development Process

### Step 1: Receive MOP from Network Team
- Method of Procedure (MOP) document provided by network engineers
- Contains:
  - List of commands to execute on nodes
  - Example outputs (success and failure scenarios)
  - Data fields to extract from outputs
  - Expected behavior and validation criteria

### Step 2: Create Activity Configuration (CSV)
**File**: `Activity_{ACTIVITY_NAME}.csv`

1. List all commands in execution order
2. For each command, define:
   - Command template with `<<<keywords>>>`
   - Parser class name (to be created in Step 4)
   - Control flow (GOTO logic)
   - Expected prompt pattern
   - Interaction/masking flags

**Example Row**:
```csv
5,"admin display-config","{""parse"": {""pbn"": [""ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_ADC""]}}","0,6;9,13",No,No,0,0,"\*?[A-Z]:\S+#"
```

**Manual Steps**:
- Write CSV locally
- Insert into database `command` table using SQL
- Associate with `CHANGE_SEQUENCE_ID`, `ACTIVITY_ID`, `DOMAIN_ID`

### Step 3: Create Input Handler (Python)
**File**: `{DOMAIN}/{ACTIVITY_NAME}_INPUT_HANDLER.py`

1. Define input Excel structure (columns needed)
2. Create `child_extract_values()` method:
   - Read Excel using pandas
   - Loop through rows
   - Build `node_pars` dictionary for each node
   - Add file paths for output/exception/connectivity CSVs
3. Create output file headers
4. Add Additional Module configuration
5. Test locally with sample Excel

**Template**:
```python
class {ACTIVITY_NAME}_INPUT_HANDLER:
    def __init__(self, input_data_map, logger_name=None):
        # Initialize variables
        pass
    
    def child_extract_values(self, input_sheet):
        # Read Excel
        # Build node_pars
        # Create output files
        return self.update_input_map()
    
    @property
    def extract_values(self):
        return self.child_extract_values(input_sheet)
    
    def run_preprocessor(self):
        return self.extract_values
```

**Manual Steps**:
- Save to `lib/ace/input_handlers/{domain}/`
- Update `input_handler_loader.py` if needed
- No hot-reload - requires server code update

### Step 4: Create Parser Logic (15+ files typically)
**Files**: `{DOMAIN}/{PARSER_CLASS_NAME}.py` (one per command)

For each command that needs parsing:

1. Analyze example outputs from MOP
2. Identify data to extract
3. Write regex patterns or parsing logic
4. Create parser class inheriting from `ParseLogic`
5. Implement `apply(command_output)` method:
   - Parse command output
   - Extract required fields
   - Update state_data_map / DYNAMIC_PARS
   - Return rcode and token_map
6. Test locally with sample outputs

**Template**:
```python
class {PARSER_CLASS_NAME}(ParseLogic):
    def __init__(self, single_node_data_map):
        super().__init__(single_node_data_map)
        self.single_node_data_map = single_node_data_map
    
    def apply(self, command_output):
        state_data_map = self.single_node_data_map["NODE_PARS"][0]
        
        # Parsing logic
        pattern = re.compile(r"Status:\s*(\w+)")
        match = pattern.search(command_output)
        
        if match:
            status = match.group(1)
            return {
                "rcode": 0,
                "token_map": {'status': status}
            }
        else:
            return {"rcode": 9}
```

**Manual Steps**:
- Save to `lib/ace/ana/parse/{domain}/`
- Test regex patterns locally
- No validation until runtime on server


### Step 5: Create Additional Module (Optional)
**File**: `lib/utils/report_utils/{MODULE_NAME}.py`

If custom post-processing needed:
1. Create module class
2. Implement `execute()` method
3. Handle CSV merging, email, calculations, etc.

**Manual Steps**:
- Save to specified directory
- Test locally if possible
- Often skipped in favor of generic `merge_csv_to_excel.py`

### Step 6: Prepare Input Sheet Template
**File**: `Input_{ACTIVITY_NAME}.xlsx`

1. Define columns matching Input Handler expectations
2. Create sample rows for testing
3. Document column purpose and format

**Manual Steps**:
- Create Excel file locally
- Share template with network team
- No validation mechanism

### Step 7: Upload All Files to Server
**Current Pain Point**: Manual file transfer

1. Connect to server via SFTP/SSH
2. Upload files to correct directories:
   - Input Handler → `/home/aceadm/ace/lib/ace/input_handlers/{domain}/`
   - Parsers (15+) → `/home/aceadm/ace/lib/ace/ana/parse/{domain}/`
   - Additional Module → `/home/aceadm/ace/lib/utils/report_utils/`
3. Restart application (sometimes required)
4. Hope no syntax errors

**NO LOCAL VALIDATION** - Syntax errors discovered at runtime!

### Step 8: Database Configuration
**Manual SQL Operations**:

1. Insert Activity record:
```sql
INSERT INTO activity (domain_id, name, description) 
VALUES (3, 'ACE_MPBN_NOKIA_SYSLOG_PRECHECK', 'Nokia Syslog Precheck');
```

2. Insert Command Sequence:
```sql
INSERT INTO command_sequence (activity_id, node_version_id, description) 
VALUES (150, 1, 'MPBN Precheck Commands');
```

3. Insert all commands from CSV:
```sql
INSERT INTO command (id, command_id, text, additional_config, goto, ...) 
VALUES (...);
-- Repeat for each command
```

4. Insert command_builder entries for keywords:
```sql
INSERT INTO command_builder (change_sequence_id, change_sequence_command_id, keyword, keyval_source) 
VALUES (5, 1, 'node_ip', 0);
-- Repeat for each keyword in each command
```

5. Link spreadsheet input handler:
```sql
UPDATE change_config SET config = '{"spreadsheet_input": {"plugin": {"pbn": ["ACE_MPBN_NOKIA_SYSLOG_PRECHECK_INPUT_HANDLER"]}}}'
WHERE activity_id = 150;
```

### Step 9: Test on Server
**Integration Testing Challenges**:

1. Upload sample input Excel to server
2. Trigger automation via frontend
3. Monitor logs in real-time:
   ```bash
   tail -f /home/aceadm/ace/output/logs/app_log/{CR_ID}/*.log
   ```
4. Discover errors:
   - **Syntax errors** (Python 2.7 compatibility)
   - **Import errors** (missing dependencies)
   - **Logic errors** (wrong regex, incorrect parsing)
   - **Variable name mismatches** (typos in keywords)
5. Fix errors directly on server (or locally and re-upload)
6. Re-run automation
7. Repeat until working

**Typical Issues Found at Runtime**:
- Indentation errors (Python 2.7 vs 3.x)
- Unicode handling issues
- Keyword case sensitivity mismatches
- Parser not returning correct structure
- Missing CSV/Excel files
- Wrong file permissions
- Database connection issues

### Step 10: UAT (User Acceptance Testing)
1. Network team tests with real nodes
2. Issues discovered:
   - Output format not as expected
   - Missing data fields in report
   - Incorrect error handling
3. Back to Step 4-9 (fix parsers, re-upload, re-test)
4. Multiple iterations until approved

## Time Estimate

| Step | Time (Typical) |
|------|----------------|
| 1. Receive MOP | 1-2 days (waiting on network team) |
| 2. Activity Config | 2-4 hours |
| 3. Input Handler | 4-6 hours |
| 4. Parser Logic (15 files) | 2-3 days |
| 5. Additional Module | 2-4 hours |
| 6. Input Sheet Template | 1 hour |
| 7. Upload to Server | 30 min |
| 8. Database Config | 1-2 hours |
| 9. Integration Testing | 2-5 days (debugging) |
| 10. UAT | 1-2 weeks (iterations) |
| **Total** | **2-4 weeks** |

## Developer Pain Points (Current System)

1. **No Local Testing Environment** - Can't run automation locally
2. **Manual File Management** - 15+ files to upload per automation
3. **Runtime Error Discovery** - Python 2.7 syntax errors found only on server
4. **Manual Database Operations** - SQL inserts prone to errors
5. **No Version Control** - Direct server edits, no Git integration
6. **Template-Based Development** - Copy-paste from previous automations
7. **Email-Based Workflows** - Reports shared via email instead of centralized system
8. **Excel Storage** - No proper database for results
9. **No CI/CD** - Manual deployment every time
10. **Debugging Difficulty** - Server logs only, no local debugging
