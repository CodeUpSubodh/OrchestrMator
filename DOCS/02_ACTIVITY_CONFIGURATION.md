# Activity Configuration Structure

## Purpose
Activity Configuration is a CSV file that defines the complete command sequence, parsing logic, control flow, and expected prompts for an automation workflow.

## File Location
- Stored in database table: `command`
- Indexed by: `node_version_id`, `id` (CHANGE_SEQUENCE_ID), `command_id`
- Example: `REFERENCE/ACTIVITY_CONFIGURATION/Activity_MPBN_PRECHECK.csv`

## CSV Column Structure

### Column 1: command_id (Sequence Number)
- Command execution order: 1, 2, 3, ...
- Sequential execution unless control flow specified

### Column 2: text (Command Template)
- The actual command to execute
- Supports variable substitution with `<<<keyword>>>` syntax
- Examples:
  ```
  ssh -o UserKnownHostsFile=/dev/null -o "StrictHostKeyChecking=false" <<<node_user>>>@<<<node_ip>>>
  show router route-table <<<syslog_ip>>>
  admin display-config
  ```
- Variables resolved from:
  - node_pars (from Input Handler)
  - DYNAMIC_PARS (from previous commands)
  - State_Data_Map

### Column 3: ADDITIONAL_CONFIG (JSON)
- Parser configuration in JSON format
- Structure: `{"parse": {"domain": ["parser_class_name"]}}`
- Example: `{"parse": {"pbn": ["ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_ADC"]}}`
- Multiple parsers can be specified:
  ```json
  {"parse": {
    "pbn": ["parser1", "parser2"],
    "ran": ["parser3"]
  }}
  ```
- Special parsers:
  - `check_success`: Generic success validator
  - Custom domain-specific parsers

### Column 4: GOTO (Control Flow)
- Format: `"success_next_cmd,failure_next_cmd;additional_condition"`
- Examples:
  - `"0,2;9,13"` - On success go to cmd 0 (exit), on failure go to cmd 2, additional condition 9→13
  - `"0,3"` - On success go to 0, on failure go to 3
  - `"0,4"` - Simple sequence
- Special values:
  - `0` = End/exit automation
  - Other numbers = Jump to that command_id

### Column 5: REQUIRE_INTERACTION
- Values: `Yes` / `No`
- If `Yes`, waits for user input during execution
- Triggers email notification to stakeholder

### Column 6: MASK_INPUT (Password Masking)
- Values: `Yes` / `No`
- If `Yes`, logs show `***` instead of actual command
- Used for password/credential commands

### Column 7-8: Timeout Configuration
- Command execution timeout values
- Default from app configuration if not specified


### Column 9: Expected Prompt (Regex)
- Regular expression pattern to match command completion
- Examples:
  - `\*?[A-Z]:\S+#` - Matches Nokia/router prompts like "A:node#"
  - `[Pp]assword\:` - Matches password prompt
  - `.*>.*` - Generic shell prompt
- Node Handler waits until this pattern appears in output before proceeding

## Example Configuration (Nokia Syslog Precheck)

```csv
1,"ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=false <<<node_user>>>@<<<node_ip>>>","{""parse"": {""pbn"": [""ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_NODE_SSH""]}}","0,2;9,13",No,No,0,0,"[Pp]assword\:"
2,"<<<node_pass>>>","{""parse"": {""pbn"": [""ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_NODE_PASS""]}}","0,3;9,13",No,Yes,0,0,"\*?[A-Z]:\S+#|[Pp]assword\:"
3,"environment time-stamp","","0,4",No,No,0,0,"\*?[A-Z]:\S+#"
4,"environment no-more","","0,5",No,No,0,0,"\*?[A-Z]:\S+#"
5,"admin display-config","{""parse"": {""pbn"": [""ACE_MPBN_NOKIA_SYSLOG_PRECHECK_PARSE_ADC""]}}","0,6;9,13",No,No,0,0,"\*?[A-Z]:\S+#"
```

## Command Builder (Variable Substitution)

### Keyword Resolution Flow
1. Extract keywords from command: `patterns.extract_keywords(command_string)`
2. For each keyword, query `command_builder` table for `keyval_source`
3. Value sources:
   - **0**: Parse from Input XML (node_pars)
   - **1**: Parse from Data Store (State_Data_Map)
   - **2**: Parse from DYNAMIC_PARS
4. Replace `<<<keyword>>>` with actual value
5. Return final command string

### Example Substitution
```python
# Template
command = "show router route-table <<<syslog_ip>>>"

# node_pars has:
node_pars = {'syslog_ip': '10.59.144.92'}

# Final command
command = "show router route-table 10.59.144.92"
```

## Control Flow Execution

### Conditional Branching
- Parser returns `rcode` (0=success, 9=failure)
- Based on rcode, next command determined from GOTO column
- Example: `"0,6;9,13"` means:
  - If rcode=0, next command is 6
  - If rcode=9, next command is 13

### Loop Support
- Command can reference itself in GOTO
- Enables retry logic or polling behavior
