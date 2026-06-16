# Parser Logic - Command Output Parsing

## Purpose
Parsers extract structured data from unstructured command outputs (CLI text, XML, JSON) and populate the State_Data_Map for use in subsequent commands or reports.

## File Location
- `lib/ace/ana/parse/{domain}/{PARSER_CLASS_NAME}.py`
- Example: `lib/ace/ana/parse/ran/ACE_BHARTI_RAN_HUAWEI_MANUAL_TT_HANDLING_dsp_n7dpc.py`
- Organized by domain: ran, core, pcn, pbn, paco, txn, core2

## Parser Class Structure

```python
from lib.ace.ana.parse.parse_logic import ParseLogic

class {PARSER_CLASS_NAME}(ParseLogic):
    def __init__(self, single_node_data_map):
        super().__init__(single_node_data_map)
        self.single_node_data_map = single_node_data_map
        self.domain = "ran"
        self.name = "Parser Name"
        self.description = "What this parser does"
        self.current_par_index = None
    
    def apply(self, command_output):
        # Main parsing logic
        # Return {"rcode": 0, "token_map": {...}} on success
        # Return {"rcode": 9} on failure
```

## Parser Workflow

### 1. Invocation
Node Handler calls parser after command execution:
```python
# From Activity Configuration
parser_config = {"parse": {"ran": ["ACE_HUAWEI_PARSER"]}}

# Node Handler loads parser
logic_handlers = logic_loader.detect_logic_handlers(
    ["parse"], ["ran"], single_node_data_map
)

# Execute parser
result = logic_handlers['parse']['ran']['ACE_HUAWEI_PARSER'].apply(command_output)
```

### 2. Access State Data
```python
def apply(self, command_output):
    state_data_map = self.single_node_data_map["NODE_PARS"][0]
    DYNAMIC_PARS = state_data_map["DYNAMIC_PARS"]
    
    # Read existing values
    circle = state_data_map["circle"]
    node_name = state_data_map["node_name"]
    cr_id = DYNAMIC_PARS["CR_ID"]
```

### 3. Parse Command Output

#### Example: Extracting Data with Regex
```python
def apply(self, command_output):
    # Pattern matching
    rc_pattern = re.compile(r"RETCODE\s*=\s*(\d+)", re.I)
    rc_match = rc_pattern.search(command_output)
    
    if rc_match and int(rc_match.group(1)) == 0:
        # Success case - extract data
        pass
    else:
        # Failure case
        return {"rcode": 9}
```

#### Example: Table Parsing
```python
# Find column indices from header
index, idx = {}, 0
for idx, line in enumerate(command_output.lower().splitlines()):
    if 'dsp name' in line and 'sccp dsp state' in line:
        index = find_index(line, pattern=r'[A-Za-z0-9][A-Za-z0-9 \[\]_-]*?(?: {2,}|$)')
        break

# Extract data using column positions
dsp_name_list = []
for line in command_output.splitlines()[idx + 1:]:
    if not line.strip(): continue
    if 'Number of results' in line: break
    
    dsp_type = line[index['dsp_type'][0]:index['dsp_type'][1]].strip()
    if dsp_type == 'A':
        dsp_name = line[index['dsp_name'][0]:index['dsp_name'][1]].strip()
        dsp_name_list.append(dsp_name)
```


### 4. Update State Data Map
```python
def apply(self, command_output):
    # ... parsing logic ...
    
    # Store extracted values in DYNAMIC_PARS
    data_storage = eval(DYNAMIC_PARS['data_storage'])
    data_storage['dsp_name_for_a_interface'] = ",".join(dsp_name_list)
    data_storage['no_of_m3ua'] = len(dsp_name_list)
    data_storage['mss_pooling'] = 'Y' if len(dsp_name_list) > 1 else 'N'
    
    return {
        "rcode": 0,
        'token_map': {
            'data_storage': data_storage
        }
    }
```

### 5. Write to Output Files
```python
def apply(self, command_output):
    # ... parsing logic ...
    
    # Write to CSV
    with open(state_data_map['remark_sheet'], 'a') as f:
        writer = csv.writer(f)
        writer.writerow([circle, node_name, 'Success', extracted_data])
    
    # Write to Excel
    wb = load_workbook(state_data_map['output_sheet_file'])
    ws = wb.active
    ws.append([node_name, node_ip, result1, result2])
    wb.save(state_data_map['output_sheet_file'])
```

### 6. Handle Errors
```python
def apply(self, command_output):
    try:
        # Parsing logic
        pass
    except Exception as ex:
        error_logs = traceback.format_exc()
        err = self.command + error_logs.splitlines()[-1]
        
        # Log to exception sheet
        AU.update_csv(remark_sheet, data=[circle, node_name, err])
        return {"rcode": 9}
```

## Common Parsing Patterns

### 1. Regex Pattern Matching
```python
# Extract single value
pattern = re.compile(r"Status:\s*(\w+)", re.I)
match = pattern.search(command_output)
if match:
    status = match.group(1)

# Extract multiple values
pattern = re.compile(r"(\d+\.\d+\.\d+\.\d+)\s+(\w+)")
matches = pattern.findall(command_output)
for ip, status in matches:
    # Process each match
```

### 2. JSON Parsing
```python
import json
data = json.loads(command_output)
value = data['key']['subkey']
```

### 3. XML Parsing
```python
import xml.etree.ElementTree as ET
root = ET.fromstring(command_output)
value = root.find('.//tag').text
```

### 4. Line-by-Line Processing
```python
for line in command_output.splitlines():
    if 'keyword' in line.lower():
        parts = line.split()
        value = parts[2]
```

## Return Value Structure

### Success Case
```python
return {
    "rcode": 0,
    "token_map": {
        'variable_name_1': 'extracted_value_1',
        'variable_name_2': 'extracted_value_2',
        'data_storage': updated_data_storage
    }
}
```

### Failure Case
```python
return {"rcode": 9}
```

## Using Parsed Values in Subsequent Commands

### In Activity Configuration
```csv
command_id,text
10,"show log log-id <<<log_id>>>"
11,"show log syslog <<<syslog_id>>>"
```

### Parser Populates DYNAMIC_PARS
```python
# Parser from command 10 extracts log_id
token_map = {'log_id': '5'}
# Node Handler merges to DYNAMIC_PARS
DYNAMIC_PARS['log_id'] = '5'
```

### Command Builder Substitutes
```python
# Command 11 template: "show log syslog <<<syslog_id>>>"
# Resolved to: "show log syslog 100"
```
