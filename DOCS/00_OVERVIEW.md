# Legacy Telecom Automation System - Complete Understanding

## Executive Summary

This document captures the complete architecture, workflow, and development process of the legacy Python 2.7 telecom automation system. The system automates network operations across telecom nodes (Nokia, Huawei, Ericsson, Cisco, Ceragon, etc.) through command execution, output parsing, and report generation.

## System Purpose

- **Primary Function**: Execute automated network operations on telecom infrastructure
- **Execution Modes**: On-demand and scheduled automation
- **Supported Vendors**: Nokia, Ericsson, Huawei, Cisco, Ceragon, Aviat, etc.
- **Output**: Excel-based reports, CSV files, logs, email notifications

## Core Components

### 1. Request Handler (`lib/ace/request_handler.py`)
- Entry point for all automation requests
- Receives XML input from frontend
- Validates authentication and authorization
- Routes requests to appropriate handlers
- Supports emergency signals (pause, resume, stop, rollback)

### 2. Change Handler (`lib/ace/change_handler.py`)
- Orchestrates workflow execution
- Manages parallel/sequential/batch execution modes
- Handles multiple nodes concurrently
- Aggregates results and generates final reports
- Calls Additional Modules for post-processing

### 3. Node Handler (`lib/ace/node_handler.py`)
- Executes commands on individual network nodes
- Maintains SSH connections to OSS/nodes
- Processes command sequences from Activity Configuration
- Applies parsing logic to command outputs
- Populates State_Data_Map for inter-command dependencies
- Generates per-node execution logs

## Document Structure

- `01_ARCHITECTURE.md` - System architecture and data flow
- `02_ACTIVITY_CONFIGURATION.md` - How automation activities are defined
- `03_INPUT_HANDLER.md` - Input processing and node_pars generation
- `04_PARSER_LOGIC.md` - Command output parsing mechanisms
- `05_ADDITIONAL_MODULE.md` - Post-processing and reporting
- `06_DEVELOPER_WORKFLOW.md` - How developers create automations
- `07_PROBLEMS_AND_PAIN_POINTS.md` - Current system limitations
- `08_MODERNIZATION_REQUIREMENTS.md` - Requirements for new system


## Key Concepts

### State_Data_Map
A dictionary structure that stores intermediate results during automation execution. Enables commands to reference outputs from previous commands using `<<<variable_name>>>` syntax.

### node_pars
A dictionary created by Input Handler containing all parameters needed for a specific node's automation execution (credentials, IPs, configuration values, file paths).

### Activity Configuration
A CSV file defining the command sequence, parsing logic, and control flow for an automation workflow.

### Parser Logic
Python classes that extract structured data from unstructured command outputs using regex, JSON, XML, or custom logic.

### Additional Module
Post-execution Python module for aggregating results, sending emails, merging CSVs to Excel, calculating conclusions.
