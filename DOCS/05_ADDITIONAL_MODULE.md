# Additional Module - Post-Processing

## Purpose
Additional Modules execute after all nodes complete, performing:
- Aggregating results from multiple CSV files
- Merging CSVs into a single Excel workbook
- Sending email notifications
- Calculating conclusions or summaries
- Custom report formatting

## File Location
- `lib/utils/report_utils/{MODULE_NAME}.py`
- Example: `REFERENCE/ADDITIONAL_MODULE/merge_csv_to_excel.py`
- Also: `lib/utils/report_utils/` contains many domain-specific modules

## Module Class Structure

```python
class {MODULE_CLASS_NAME}:
    def __init__(self, additional_reporting_data):
        self.additional_reporting_data = additional_reporting_data
    
    def execute(self):
        # Post-processing logic
        pass

def get_module_object(additional_reporting_data):
    return {MODULE_CLASS_NAME}(additional_reporting_data)
```

## Configuration in Input Handler

```python
additional_module_data = {
    'custom_reporting_class_name': 'MergeCSVtoExcel',
    'custom_reporting_module_name': 'merge_csv_to_excel',
    'additional_reporting_data': {
        'report_file_excel': '/archive/12345/reports/FINAL_REPORT.xlsx',
        'sheet_name_to_csv_mapping': [
            ('Connectivity', '/archive/12345/reports/CONNECTIVITY.csv'),
            ('Exception', '/archive/12345/reports/EXCEPTION.csv'),
            ('Results', '/archive/12345/reports/OUTPUT.csv')
        ]
    }
}

# Add to node_pars
node_pars[node_name][0]['custom_reporting_module_data'] = additional_module_data
```

## Execution Flow

### 1. Change Handler Triggers
After all Node Handlers complete:
```python
# In change_handler.py
if 'custom_reporting_module_data' in node_pars[node_name][0]:
    module_data = node_pars[node_name][0]['custom_reporting_module_data']
    module_name = module_data['custom_reporting_module_name']
    class_name = module_data['custom_reporting_class_name']
    additional_data = module_data['additional_reporting_data']
    
    # Dynamically import module
    module = __import__(module_name)
    module_obj = module.get_module_object(additional_data)
    module_obj.execute()
```

### 2. Module Execution
```python
class MergeCSVtoExcel:
    def __init__(self, additional_reporting_data):
        self.report_file_excel = additional_reporting_data['report_file_excel']
        self.sheet_mappings = additional_reporting_data['sheet_name_to_csv_mapping']
    
    def execute(self):
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        for sheet_name, csv_file in self.sheet_mappings:
            ws = wb.create_sheet(title=sheet_name)
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        ws.append(row)
        
        wb.save(self.report_file_excel)
```

## Common Additional Modules

### 1. CSV to Excel Merger
- Combines multiple CSV files into Excel workbook
- Each CSV becomes a separate sheet
- Handles missing files gracefully


### 2. Email Notification Module
```python
class EmailNotificationModule:
    def execute(self):
        mailer = mail_utils.MailUtils(smtp_server, from_email)
        
        subject = f"Automation Report - CR#{cr_id}"
        body = f"Automation completed. {success_count} successful, {fail_count} failed."
        
        mailer.send_mail_html(recipient_email, subject, reply_to, body)
        
        # Attach Excel report
        mailer.send_mail_with_attachment(recipient_email, subject, body, report_file)
```

### 3. Pre-Post Comparison Module
```python
class PrePostComparisonModule:
    def execute(self):
        pre_data = self.read_csv(pre_check_file)
        post_data = self.read_csv(post_check_file)
        
        comparison_results = []
        for node in pre_data:
            if node in post_data:
                diff = self.compare(pre_data[node], post_data[node])
                comparison_results.append([node, diff['status'], diff['changes']])
        
        self.write_comparison_report(comparison_results)
```

### 4. Dashboard/Metrics Module
```python
class DashboardModule:
    def execute(self):
        # Aggregate statistics
        total_nodes = len(node_list)
        success_rate = (success_count / total_nodes) * 100
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        # Generate charts (using matplotlib/openpyxl)
        self.create_pie_chart(success_count, fail_count)
        self.create_timeline_chart(node_execution_data)
        
        # Write to dashboard Excel
        self.write_dashboard(metrics_data)
```

### 5. Conclusion Calculator Module
```python
class ConclusionModule:
    def execute(self):
        # Read all node results
        results = self.read_all_results()
        
        # Calculate overall status
        if all(r['status'] == 'Success' for r in results):
            conclusion = 'PASS - All nodes completed successfully'
        elif any(r['critical_error'] for r in results):
            conclusion = 'CRITICAL FAIL - Critical errors detected'
        else:
            conclusion = f'PARTIAL PASS - {success_count}/{total_count} nodes successful'
        
        # Write conclusion to summary sheet
        self.write_conclusion(conclusion)
```

## Integration with Change Handler

### Final Report Generation
After Additional Module execution:
```python
# Change Handler compiles final report
final_report = []
final_report.append(report_headers)

for record in input_records:
    for report_line in node_data_map[record["INDEX"]]["ACTIVITY_REPORT"]:
        final_report.append(report_line)

report_string = '\n'.join(final_report)

# Update database
cr_insert_query = db.build_insert("change_report", 
                                  [cr_id, "NULL", report_string], True)
db.run_query(cr_insert_query)
```

### Email Notification Flow
```python
# Change Handler sends final notification
summary = f"CR #{cr_id} completed. Success: {success_ctr}, Failed: {fail_ctr}"

mailer.send_mail_html(
    to=fe_email_id,
    subject=f"Automation Complete - CR#{cr_id}",
    body=summary,
    attachments=[final_report_excel]
)
```

## Error Handling in Additional Modules

```python
def execute(self):
    try:
        # Module logic
        self.process_data()
        self.generate_reports()
    except Exception as e:
        # Log error but don't fail entire automation
        print(f"Additional Module Error: {str(e)}")
        
        # Write error to exception log
        with open(exception_log, 'a') as f:
            f.write(f"{datetime.now()},{module_name},{str(e)}\n")
```

## Custom Module Development

### Template
```python
class CustomModule:
    def __init__(self, additional_reporting_data):
        self.data = additional_reporting_data
        self.input_file = self.data.get('input_file')
        self.output_file = self.data.get('output_file')
    
    def execute(self):
        # Read inputs
        data = self.read_data()
        
        # Process
        processed = self.process(data)
        
        # Write outputs
        self.write_output(processed)
    
    def read_data(self):
        pass
    
    def process(self, data):
        pass
    
    def write_output(self, processed):
        pass

def get_module_object(additional_reporting_data):
    return CustomModule(additional_reporting_data)
```
