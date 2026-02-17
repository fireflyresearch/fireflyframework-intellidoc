# Examples

**fireflyframework-intellidoc — Document Type & Processing Examples**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

This guide provides complete examples for common IDP use cases. Each example
shows how to create the document type, define catalog fields, assign default
fields, set up validators, and process documents.

## 1. Invoice Processing

### Document Type

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice",
    "name": "Commercial Invoice",
    "description": "A commercial invoice for goods or services rendered with line items and payment details",
    "nature": "financial",
    "visual_description": "A formal document with a company logo at the top, an invoice number, billing and shipping addresses, a table of line items with descriptions, quantities, and prices, and totals at the bottom",
    "visual_cues": [
      "company logo or letterhead",
      "invoice number prominently displayed",
      "table with columns for items, quantities, prices",
      "subtotal, tax, and total amount",
      "billing and shipping addresses",
      "payment terms or due date"
    ],
    "sample_keywords": ["invoice", "bill to", "ship to", "total", "subtotal", "tax", "due date", "quantity", "amount"],
    "classification_confidence_threshold": 0.75
  }'
```

### Catalog Fields

```bash
# Create invoice fields (these are reusable across document types)
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "invoice_number", "display_name": "Invoice Number", "field_type": "text", "required": true, "location_hint": "Near the top right"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "invoice_date", "display_name": "Invoice Date", "field_type": "date", "required": true, "format_pattern": "YYYY-MM-DD"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "total_amount", "display_name": "Total", "field_type": "currency", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "vendor_name", "display_name": "Vendor", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "customer_name", "display_name": "Customer", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "line_items", "display_name": "Line Items", "field_type": "table", "required": true, "table_columns": [{"code": "description", "display_name": "Description", "field_type": "text"}, {"code": "quantity", "display_name": "Qty", "field_type": "number"}, {"code": "unit_price", "display_name": "Unit Price", "field_type": "currency"}, {"code": "amount", "display_name": "Amount", "field_type": "currency"}]}'

# Assign default fields to the invoice document type
curl -X PUT http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["invoice_number", "invoice_date", "total_amount", "vendor_name", "customer_name", "line_items"]}'
```

### Validators

```bash
# Total = Subtotal + Tax
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_total_sum",
    "name": "Total = Subtotal + Tax",
    "description": "Verify total amount equals subtotal plus tax amount within tolerance",
    "validator_type": "cross_field",
    "severity": "warning",
    "config": {"type": "sum", "fields": ["subtotal", "tax_amount"], "total_field": "total_amount", "tolerance": 0.01}
  }'

# Date ordering
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_dates_valid",
    "name": "Invoice Date <= Due Date",
    "description": "Ensure invoice date is before or equal to due date",
    "validator_type": "cross_field",
    "severity": "warning",
    "config": {"type": "date_order", "fields": ["invoice_date", "due_date"]}
  }'
```

---

## 2. Identity Document Processing

### Passport

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "passport",
    "name": "Passport",
    "description": "Government-issued passport used for international identification and travel",
    "nature": "identity",
    "visual_description": "A booklet-style identity document with a photo of the holder, personal details printed in a standardized format, and a machine-readable zone (MRZ) at the bottom with two lines of encoded text",
    "visual_cues": [
      "passport photo of the holder",
      "country name and coat of arms",
      "machine-readable zone (MRZ) at bottom",
      "passport number",
      "date of birth and expiry date",
      "nationality"
    ],
    "sample_keywords": ["passport", "surname", "given names", "nationality", "date of birth", "date of expiry", "MRZ"],
    "classification_confidence_threshold": 0.85
  }'
```

**Catalog Fields:**
```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "passport_number", "display_name": "Passport Number", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "surname", "display_name": "Surname", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "given_names", "display_name": "Given Names", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "nationality", "display_name": "Nationality", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "date_of_birth", "display_name": "Date of Birth", "field_type": "date", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "date_of_expiry", "display_name": "Date of Expiry", "field_type": "date", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "mrz_line_1", "display_name": "MRZ Line 1", "field_type": "text", "location_hint": "Bottom of the data page"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "mrz_line_2", "display_name": "MRZ Line 2", "field_type": "text", "location_hint": "Bottom of the data page"}'

# Assign to passport document type
curl -X PUT http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["passport_number", "surname", "given_names", "nationality", "date_of_birth", "date_of_expiry", "mrz_line_1", "mrz_line_2"]}'
```

**Validators:**
```bash
# Photo must be present
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "passport_has_photo",
    "name": "Photo Present",
    "description": "Verify that the passport contains a visible photo of the holder",
    "validator_type": "visual",
    "severity": "error",
    "visual_prompt": "Is there a clearly visible photo of a person on this document?",
    "visual_expected": "A passport-style photo of the document holder",
    "applicable_natures": ["identity"]
  }'

# Passport not expired
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "passport_not_expired",
    "name": "Not Expired",
    "description": "Check that the passport expiry date is in the future",
    "validator_type": "business_rule",
    "severity": "error",
    "config": {"expression": "date_of_expiry > today()"}
  }'

# Issue date before expiry
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "passport_date_order",
    "name": "Issue Before Expiry",
    "description": "Issue date must be before expiry date",
    "validator_type": "cross_field",
    "severity": "error",
    "config": {"type": "date_order", "fields": ["date_of_issue", "date_of_expiry"]}
  }'
```

### Driver's License

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "drivers_license",
    "name": "Driver'\''s License",
    "description": "Government-issued driver'\''s license or driving permit used for identification and driving authorization",
    "nature": "identity",
    "visual_description": "A card-sized identity document with a photo, personal details, license number, categories, and often a barcode on the back",
    "visual_cues": [
      "photo of the holder",
      "license number",
      "vehicle categories or class",
      "date of birth and expiry",
      "issuing state or country",
      "barcode or QR code on reverse"
    ],
    "sample_keywords": ["driver", "license", "class", "DOB", "expiry", "restrictions", "endorsements"]
  }'
```

---

## 3. Medical Documents

### Lab Report

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "lab_report",
    "name": "Laboratory Report",
    "description": "Clinical laboratory test results report containing patient information, test names, values, reference ranges, and findings",
    "nature": "medical",
    "visual_description": "A clinical document with a laboratory or hospital letterhead, patient demographics, and a structured table of test names, measured values, units, reference ranges, and flags for abnormal results",
    "visual_cues": [
      "laboratory or hospital logo",
      "patient name and date of birth",
      "table of test results with values and ranges",
      "abnormal result flags (H, L, or highlighting)",
      "specimen collection date",
      "ordering physician name"
    ],
    "sample_keywords": ["laboratory", "test results", "reference range", "specimen", "patient", "physician"]
  }'
```

**Catalog Fields:**
```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "patient_name", "display_name": "Patient Name", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "collection_date", "display_name": "Collection Date", "field_type": "date", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "test_results", "display_name": "Test Results", "field_type": "table", "required": true, "table_columns": [{"code": "test_name", "display_name": "Test", "field_type": "text"}, {"code": "result", "display_name": "Result", "field_type": "text"}, {"code": "unit", "display_name": "Unit", "field_type": "text"}, {"code": "reference_range", "display_name": "Reference Range", "field_type": "text"}, {"code": "flag", "display_name": "Flag", "field_type": "enum", "allowed_values": ["normal", "high", "low", "critical"]}]}'

# Assign to lab report document type
curl -X PUT http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["patient_name", "collection_date", "test_results"]}'
```

---

## 4. Real Estate Documents

### Lease Agreement

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "lease_agreement",
    "name": "Residential Lease Agreement",
    "description": "A legally binding contract between a landlord and tenant for the rental of a residential property",
    "nature": "real_estate",
    "visual_description": "A multi-page legal document with a title like Lease Agreement or Rental Agreement, parties section listing landlord and tenant, property address, lease terms, rent amount, and signature blocks",
    "visual_cues": [
      "title: Lease Agreement or Rental Agreement",
      "parties section (landlord and tenant names)",
      "property address",
      "lease term dates",
      "monthly rent amount",
      "security deposit amount",
      "signature lines at the end"
    ],
    "sample_keywords": ["lease", "tenant", "landlord", "rent", "security deposit", "premises", "term"]
  }'
```

**Catalog Fields:**
```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "landlord_name", "display_name": "Landlord", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "tenant_name", "display_name": "Tenant", "field_type": "text", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "property_address", "display_name": "Property Address", "field_type": "address", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "monthly_rent", "display_name": "Monthly Rent", "field_type": "currency", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "lease_start_date", "display_name": "Start Date", "field_type": "date", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "lease_end_date", "display_name": "End Date", "field_type": "date", "required": true}'

# Assign to lease document type
curl -X PUT http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["landlord_name", "tenant_name", "property_address", "monthly_rent", "lease_start_date", "lease_end_date"]}'
```

**Validators:**
```bash
# Lease dates valid
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "lease_dates_valid",
    "name": "Lease Dates Valid",
    "description": "Start date must be before end date",
    "validator_type": "cross_field",
    "severity": "error",
    "config": {"type": "date_order", "fields": ["lease_start_date", "lease_end_date"]}
  }'

# Signatures present
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "lease_has_signatures",
    "name": "Signatures Present",
    "description": "Verify that the lease contains signatures from both parties",
    "validator_type": "visual",
    "severity": "error",
    "visual_prompt": "Are there two or more handwritten signatures visible on this document?",
    "visual_expected": "Handwritten signatures from landlord and tenant",
    "applicable_natures": ["real_estate"]
  }'
```

---

## 5. Multi-Document Batch Processing

Process a folder of mixed documents with automatic classification:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "source_type": "local",
        "source_reference": "/documents/doc-001.pdf",
        "filename": "doc-001.pdf",
        "tags": {"batch": "january-2026", "department": "finance"}
      },
      {
        "source_type": "local",
        "source_reference": "/documents/doc-002.pdf",
        "filename": "doc-002.pdf",
        "tags": {"batch": "january-2026", "department": "finance"}
      },
      {
        "source_type": "s3",
        "source_reference": "s3://company-docs/incoming/doc-003.pdf",
        "filename": "doc-003.pdf",
        "tags": {"batch": "january-2026", "department": "hr"}
      },
      {
        "source_type": "url",
        "source_reference": "https://partner.example.com/api/documents/inv-2026-001.pdf",
        "filename": "inv-2026-001.pdf",
        "expected_nature": "financial",
        "tags": {"batch": "january-2026", "source": "partner-api"}
      }
    ],
    "stop_on_failure": false
  }'
```

Monitor batch progress:
```bash
# List all jobs from the batch
curl "http://localhost:8080/api/v1/intellidoc/jobs?from_date=2026-01-15T00:00:00&size=100"

# Check a specific job
curl http://localhost:8080/api/v1/intellidoc/jobs/{job_id}/status
```

---

## 6. Custom Validator Examples

### Email Format Validator

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "valid_email",
    "name": "Valid Email Address",
    "description": "Validates that extracted email addresses are properly formatted",
    "validator_type": "format",
    "severity": "error",
    "config": {"type": "email"},
    "applicable_fields": ["email", "contact_email", "billing_email"]
  }'
```

### IBAN Validator

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "valid_iban",
    "name": "Valid IBAN",
    "description": "Validates IBAN format and MOD97 checksum",
    "validator_type": "format",
    "severity": "error",
    "config": {"type": "iban"},
    "applicable_fields": ["iban", "bank_account"]
  }'
```

### Custom Regex Validator

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "us_ssn_format",
    "name": "US SSN Format",
    "description": "Validates US Social Security Number format (XXX-XX-XXXX)",
    "validator_type": "format",
    "severity": "error",
    "config": {"type": "regex", "pattern": "^\\d{3}-\\d{2}-\\d{4}$"},
    "applicable_fields": ["ssn", "social_security_number"]
  }'
```

### Visual Stamp Validator

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "has_official_stamp",
    "name": "Official Stamp Present",
    "description": "Verify that the document has an official stamp or seal",
    "validator_type": "visual",
    "severity": "warning",
    "visual_prompt": "Is there an official stamp, seal, or embossed mark visible on this document?",
    "visual_expected": "An official government or corporate stamp/seal",
    "applicable_natures": ["government", "legal"]
  }'
```

### Business Rule Validator

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "discount_limit",
    "name": "Discount Within Limits",
    "description": "Total discount should not exceed 30% of subtotal",
    "validator_type": "business_rule",
    "severity": "warning",
    "config": {"expression": "total_discount <= subtotal * 0.3"},
    "applicable_natures": ["financial", "commercial"]
  }'
```

---

## 7. Multi-Document File with Visual Splitting

When a single PDF contains multiple documents (e.g., a scanned batch):

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/scans/batch-scan-2026-01.pdf",
    "filename": "batch-scan-2026-01.pdf",
    "splitting_strategy": "visual",
    "async_mode": true,
    "tags": {"source": "scanner", "batch_date": "2026-01-15"}
  }'
```

The visual splitter will:
1. Analyze each page using a VLM
2. Detect boundaries where one document ends and another begins
3. Group pages into individual documents
4. Each detected document is classified, extracted, and validated independently

The result will contain multiple `documents` entries:
```json
{
  "documents": [
    {"document_type_code": "invoice", "page_range_start": 1, "page_range_end": 2, ...},
    {"document_type_code": "receipt", "page_range_start": 3, "page_range_end": 3, ...},
    {"document_type_code": "invoice", "page_range_start": 4, "page_range_end": 5, ...}
  ]
}
```

---

## 8. Processing with Expected Type (Binary Classification Hint)

When you know the expected document type, provide it as a binary classification hint:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "url",
    "source_reference": "https://api.vendor.com/invoices/2026/inv-0042.pdf",
    "filename": "inv-0042.pdf",
    "expected_type": "invoice",
    "splitting_strategy": "page_based"
  }'
```

The VLM performs a focused binary classification — "is this document an invoice?" — rather
than comparing against all catalog types. If the type exists in the catalog, its default
fields are used for extraction. You can also combine `expected_type` with inline fields:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/invoice.pdf",
    "filename": "invoice.pdf",
    "expected_type": "invoice",
    "target_schema": {
      "inline_fields": [
        {"name": "invoice_number", "display_name": "Invoice Number", "field_type": "text", "required": true},
        {"name": "total_amount", "display_name": "Total", "field_type": "currency"}
      ]
    }
  }'
```

This performs binary classification and extracts only the two specified fields.

---

## 9. Narrowing Classification with Expected Nature

When you know the general category but not the specific type:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/unknown-financial-doc.pdf",
    "filename": "unknown-financial-doc.pdf",
    "expected_nature": "financial"
  }'
```

This narrows the classification to only consider document types with
nature `financial` (e.g., invoice, receipt, bank statement, tax form),
improving accuracy and speed.

---

## 10. Using Inline Fields (Ad-Hoc Extraction)

Extract fields that aren't in the catalog using inline definitions:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/receipt.jpg",
    "filename": "receipt.jpg",
    "target_schema": {
      "field_codes": ["vendor_name", "total_amount"],
      "inline_fields": [
        {
          "name": "payment_method",
          "display_name": "Payment Method",
          "field_type": "text",
          "description": "How the purchase was paid (cash, credit card, etc.)"
        },
        {
          "name": "store_location",
          "display_name": "Store Location",
          "field_type": "address",
          "description": "Physical address of the store"
        }
      ]
    }
  }'
```

This combines catalog fields (`vendor_name`, `total_amount`) with ad-hoc inline fields (`payment_method`, `store_location`). When inline fields are present, they take the highest priority in field resolution — the system uses them instead of catalog defaults.

> **Note:** Inline fields can be used without any catalog setup at all. When only `inline_fields` are provided (no `field_codes`), classification is skipped and extraction runs directly from the inline schema.

---

## 11. Field-Level Validation Rules

Embed validation rules directly in catalog field definitions using `validation_rules`.
These travel with the field and run automatically during the validation step — no need
to create separate `ValidatorDefinition` entries for simple per-field checks.

### Fields with Embedded Validation

```bash
# Email field with format validation
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "contact_email",
    "display_name": "Contact Email",
    "field_type": "email",
    "required": true,
    "validation_rules": [
      {
        "rule_type": "required",
        "severity": "error",
        "message": "Contact email is required"
      },
      {
        "rule_type": "format",
        "severity": "error",
        "config": {"type": "email"},
        "message": "Must be a valid email address"
      }
    ]
  }'

# Numeric field with range validation
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "discount_percent",
    "display_name": "Discount Percentage",
    "field_type": "number",
    "min_value": 0,
    "max_value": 100,
    "validation_rules": [
      {
        "rule_type": "range",
        "severity": "error",
        "config": {"min": 0, "max": 100},
        "message": "Discount must be between 0% and 100%"
      }
    ]
  }'

# Text field with regex format validation
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "po_number",
    "display_name": "Purchase Order Number",
    "field_type": "text",
    "validation_rules": [
      {
        "rule_type": "format",
        "severity": "warning",
        "config": {"type": "regex", "pattern": "^PO-\\d{4,8}$"},
        "message": "PO number should match PO-XXXX format"
      }
    ]
  }'

# IBAN field with checksum validation
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "bank_iban",
    "display_name": "Bank IBAN",
    "field_type": "text",
    "validation_rules": [
      {
        "rule_type": "checksum",
        "severity": "error",
        "config": {"type": "iban"},
        "message": "Invalid IBAN — checksum verification failed"
      }
    ]
  }'
```

### When to Use Field-Level vs Document-Type Validators

| Use case | Approach | Why |
|---|---|---|
| Field format check (email, regex, IBAN) | Field-level `validation_rules` | Rule belongs with the field definition and applies everywhere the field is used |
| Required field check | Field-level `validation_rules` | Tied to the field semantics, not the document type |
| Cross-field logic (total = subtotal + tax) | Document-type `ValidatorDefinition` | Involves multiple fields — can't be attached to a single field |
| Visual check (signature present) | Document-type `ValidatorDefinition` | Relates to the document as a whole, not a specific field |
| Business rule (discount < 30% of subtotal) | Document-type `ValidatorDefinition` | Complex expression spanning multiple fields |

Both levels run through the same `ValidationEngine` and produce the same `ValidationResult`
objects. Field-level rules are automatically converted to ephemeral `ValidatorDefinition`
objects at validation time, scoped to the field's code via `applicable_fields`.

---

## 12. Ad-Hoc Document Types (Runtime Classification)

Classify documents against types defined at request time — no catalog needed:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/document.pdf",
    "filename": "document.pdf",
    "document_types": [
      {
        "code": "invoice",
        "description": "A formal payment request with line items, totals, and payment details",
        "nature": "financial"
      },
      {
        "code": "receipt",
        "description": "A proof of purchase from a store or vendor, usually compact with a total",
        "nature": "financial"
      },
      {
        "code": "contract",
        "description": "A legal agreement between parties with terms, conditions, and signatures",
        "nature": "legal"
      }
    ],
    "target_schema": {
      "inline_fields": [
        {"name": "document_date", "display_name": "Date", "field_type": "date"},
        {"name": "total_amount", "display_name": "Amount", "field_type": "currency"},
        {"name": "counterparty", "display_name": "Other Party", "field_type": "text"}
      ]
    }
  }'
```

The VLM classifies against the three ad-hoc types and extracts the inline fields. No catalog
setup is required. Ad-hoc types can also be combined with catalog types — they are merged
into a single classification candidate list.

**CLI equivalent:**
```bash
intellidoc process document.pdf \
    --document-types "invoice:Payment request with line items,receipt:Proof of purchase,contract:Legal agreement" \
    --schema "document_date:date,total_amount:currency,counterparty:text"
```

---

## 13. Extraction-Only Mode (No Classification)

When you only need to extract specific fields and don't care about document classification,
provide only inline fields. Classification is skipped entirely:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/receipt.jpg",
    "filename": "receipt.jpg",
    "target_schema": {
      "inline_fields": [
        {"name": "vendor", "display_name": "Vendor Name", "field_type": "text", "required": true},
        {"name": "amount", "display_name": "Total Amount", "field_type": "currency", "required": true},
        {"name": "date", "display_name": "Purchase Date", "field_type": "date"},
        {"name": "items", "display_name": "Items", "field_type": "list", "description": "List of purchased items"}
      ]
    }
  }'
```

This is the simplest mode — just define what you want to extract and send the document.
No catalog, no document types, no classification step.

**CLI equivalent:**
```bash
intellidoc process receipt.jpg \
    --schema "vendor:text,amount:currency,date:date,items:list"
```

---

## 14. Mixed Mode (Catalog + Runtime Types)

Combine catalog document types with ad-hoc types for maximum flexibility. This is useful
when your catalog covers common document types but you occasionally encounter new types:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/uploads/unknown-doc.pdf",
    "filename": "unknown-doc.pdf",
    "document_types": [
      {
        "code": "utility_bill",
        "description": "A monthly utility bill for electricity, water, or gas",
        "nature": "financial"
      }
    ],
    "target_schema": {
      "inline_fields": [
        {"name": "account_number", "display_name": "Account Number", "field_type": "text"},
        {"name": "amount_due", "display_name": "Amount Due", "field_type": "currency"},
        {"name": "due_date", "display_name": "Due Date", "field_type": "date"}
      ]
    }
  }'
```

The classification runs against all catalog types **plus** the ad-hoc `utility_bill` type.
Because inline fields are provided, they take priority over catalog default fields regardless
of which type is matched.

**CLI equivalent:**
```bash
intellidoc process unknown-doc.pdf \
    --document-types "utility_bill:Monthly utility bill for electricity or gas" \
    --schema "account_number:text,amount_due:currency,due_date:date"
```

---

## 15. CLI Dynamic Processing Examples

All examples above use the REST API. Here are equivalent CLI commands for common operations.
The CLI uses the same processing engine — see the [CLI Reference](cli.md) for full documentation.

All examples above use the REST API. Here are equivalent CLI commands for common operations.
The CLI uses the same processing engine — see the [CLI Reference](cli.md) for full documentation.

### Single Document Processing

```bash
# Process an invoice (auto-classify, extract default fields)
intellidoc process invoice.pdf

# With a specific model
intellidoc process invoice.pdf --model openai:gpt-4o

# Extract only specific fields
intellidoc process invoice.pdf --fields invoice_number,total_amount,vendor_name

# Binary classification hint
intellidoc process invoice.pdf --expected-type invoice

# Narrow classification to financial documents
intellidoc process unknown-doc.pdf --expected-nature financial

# Pretty JSON output
intellidoc process invoice.pdf --pretty

# Table output
intellidoc process invoice.pdf --format table

# Save results to file
intellidoc process invoice.pdf --pretty --output result.json
```

### Dynamic Pipeline (No Catalog)

```bash
# Extraction-only — define fields inline, no classification
intellidoc process invoice.pdf \
    --schema "invoice_number:text,total_amount:currency,vendor:text,date:date"

# Ad-hoc types + inline schema
intellidoc process document.pdf \
    --document-types "invoice:Payment request,receipt:Proof of purchase" \
    --schema "amount:currency,vendor:text"

# Binary classification + inline schema
intellidoc process invoice.pdf \
    --expected-type invoice \
    --schema "invoice_number:text,amount:currency"

# Schema from a JSON file
intellidoc process invoice.pdf --schema @fields.json

# Document types from a JSON file
intellidoc process document.pdf --document-types @types.json --schema @fields.json
```

### Batch Processing

```bash
# Process all documents in a directory
intellidoc batch ./invoices/

# Save per-file results to an output directory
intellidoc batch ./invoices/ --output ./results/ --format json

# All files are invoices — binary classification hint
intellidoc batch ./invoices/ --expected-type invoice

# Batch with inline schema (no catalog needed)
intellidoc batch ./receipts/ --schema "vendor:text,amount:currency,date:date"

# Batch with ad-hoc types + schema
intellidoc batch ./mixed/ \
    --document-types "invoice:Payment request,receipt:Proof of purchase" \
    --schema "amount:currency,vendor:text"

# Use Anthropic model with table output
intellidoc batch ./documents/ --model anthropic:claude-sonnet-4-5-20250929 --format table

# Quiet mode for scripting
intellidoc batch ./incoming/ --quiet --output ./processed/
```

### Catalog Management

```bash
# Validate a catalog YAML file
intellidoc catalog validate catalog.yaml

# Display catalog contents as a table
intellidoc catalog show catalog.yaml

# Display catalog as JSON
intellidoc catalog show catalog.yaml --format json
```

### Scripting and Pipelines

```bash
# Pipe JSON output to jq
intellidoc process invoice.pdf --quiet | jq '.documents[0].fields'

# Extract a single field value
TOTAL=$(intellidoc process invoice.pdf --quiet --fields total_amount \
  | jq -r '.documents[0].fields.total_amount')
echo "Total: $TOTAL"

# Validate catalog before deployment
intellidoc catalog validate catalog.yaml || exit 1
```
