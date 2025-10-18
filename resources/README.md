# Resources

This directory stores additional resources for the incident resolution system.

## Purpose

This directory is for supplementary resources that don't fit into the knowledge base, such as:

- Configuration files
- Templates
- Scripts
- Data files
- Cache files
- Temporary artifacts

## Access

Resources stored here can be accessed through the MCP server using:

- `resources://available` - Lists all available resources

## Usage

The orchestration agent can reference these resources when coordinating incident resolution tasks. Future implementations may include specific resource handlers for different file types.

## Organization

Consider organizing resources by type:

```
resources/
├── configs/
├── templates/
├── scripts/
└── data/
```
