# Database Dictionary (data/contracts.db)

## contracts
- `id` (PK)
- `record_uid` (unique) – internal UID generated on insert
- `contract_number` (indexed) – contract code/number
- `title` – contract title
- `contract_amount`, `currency`
- `customer_name`
- `project_code`
- `signed_at`
- `description`
- `status`
- `tags`
- `industry`
- `harvest_context` – crawl context: contract_type + date range + page
- `raw_payload` (JSON) – raw scraped payload
- `borrow_materials` – e.g., “合同｜发票”
- `collected_at`, `created_at`, `updated_at`
- `data_status`

## harvest_logs
- `id` (PK)
- `category` (contract / qualification / ip)
- `company_name` (for company-based crawls)
- `contract_type`
- `year`
- `start_date`, `end_date`
- `pages_scraped`, `records_scraped`, `pages_committed`, `records_committed`
- `expected_pages`, `expected_records`
- `status` (success / failure / …)
- `message`
- `started_at`, `completed_at`, `created_at`
- Unique: (`category`, `contract_type`, `company_name`, `start_date`, `end_date`)

## qualification_assets
- `id` (PK)
- `record_uid` (unique) – internal UID
- `company_name`, `company_code`, `business_type`
- `qualification_name`, `qualification_level`
- `expire_date`, `next_review_date`
- `internal_id`
- `patent_category`
- `registration_no`
- `certificate_number`
- `issuer`, `issue_date`
- `status`
- `keeper`
- `remark`
- `download_url`
- `raw_payload` (JSON)
- `created_at`, `updated_at`
- `data_status`

## intellectual_property_assets
- `id` (PK)
- `record_uid` (unique) – internal UID
- `company_name`, `company_code`, `business_type`
- `knowledge_category`, `patent_category`
- `knowledge_name`
- `certificate_number`
- `inventor`
- `issue_date`, `application_date`
- `internal_id`
- `property_summary`
- `application_status`
- `issuer`
- `version`
- `registration_no`
- `download_url`
- `raw_payload` (JSON)
- `created_at`, `updated_at`
- `data_status`

## companies
- `id` (PK)
- `name` (unique)
- `business_type`
- `total_count` – aggregate count from company page
- `code`
- `qualification_count`, `ip_count`
- `created_at`, `updated_at`
- `data_status`

## harvest_warnings
- `id` (PK)
- `category` (contract / qualification / ip)
- `company_name`
- `contract_type`
- `year`
- `start_date`, `end_date`
- `page_number`
- `warning_type` (e.g., parse_mismatch / insert_mismatch / split_limit)
- `details`
- `field_name`
- `file_name`
- `retry_count`
- `created_at`

## harvest_tasks
- `id` (PK)
- `category`
- `contract_type`
- `start_date`, `end_date`
- `company_name`
- `status` (未开始 / 进行中 / 已拆分 / 已结束 / 任务中断)
- `remark`
- `current_page` – last processed page for resume
- `target_pages` – specific pages to rerun
- `created_at`, `updated_at`
- Unique: (`category`, `contract_type`, `company_name`, `start_date`, `end_date`)
