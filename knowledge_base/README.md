# Knowledge Base

This directory stores PDF documents and other reference materials for the incident resolution system.

## Purpose

The orchestration agent accesses documents stored here to:

- Retrieve incident resolution procedures
- Access troubleshooting guides
- Reference system documentation
- Query historical incident reports

## Adding Documents

Simply place your PDF files and other documents in this directory. The orchestration agent will automatically detect them through the following resources:

- `knowledge-base://pdfs` - Lists all PDF files
- `knowledge-base://documents` - Lists all documents (any format)

## Supported Formats

While the MCP server currently supports listing any file type, PDF documents are the primary format for the knowledge base. Future versions may include:

- PDF parsing and search capabilities
- Document indexing
- Content extraction and summarization

## Example Usage

1. Add a PDF: `incident_procedures.pdf`
2. The orchestration agent will detect it automatically
3. Access it through the MCP resource: `knowledge-base://pdfs`

## Notes

- Keep documents well-organized with clear filenames
- Use descriptive names (e.g., `server_troubleshooting_guide.pdf`)
- Large documents are supported but may affect performance
- Consider splitting very large documents into smaller, topic-specific files
