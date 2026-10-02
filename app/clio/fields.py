"""Explicit `fields=` selections for each Clio v4 list endpoint.

Clio v4 returns only `id` and `etag` unless fields are named. These lists come from the
`*_base` schemas in https://docs.developers.clio.com/openapi.json (fetched 2026-10-02).
Nested relations ask only for ids and display names; the full records come from their own endpoint.
Clio allows only one level of nesting in `fields` (`a{b{c}}` is rejected with InvalidFields).
"""

REF = "{id,name}"
PARTICIPANT = "{id,name,type,identifier}"

CUSTOM_FIELD_VALUES = (
    "custom_field_values{id,field_name,field_type,field_required,field_displayed,"
    "field_display_order,value,soft_deleted,created_at,updated_at}"
)

MATTER = ",".join([
    "id,etag,number,display_number,custom_number,description,status,location,client_reference,"
    "client_id,billable,billing_method,open_date,close_date,pending_date,created_at,updated_at,"
    "shared,has_tasks,last_activity_date,matter_stage_updated_at",
    "client{id,name,type}",
    "matter_stage{id,name,order,practice_area_id}",
    f"practice_area{{id,name,category,code}}",
    f"responsible_attorney{REF}",
    f"originating_attorney{REF}",
    f"responsible_staff{REF}",
    "statute_of_limitations{id,name,due_at,status}",
    "folder{id,name,root}",
    "relationships{id,description}",
    CUSTOM_FIELD_VALUES,
])

MATTER_LIST = "id,display_number,description,status,client{id,name},matter_stage{id,name},open_date"

MATTER_STAGE = "id,etag,practice_area_id,name,order,created_at,updated_at"

CUSTOM_FIELD = (
    "id,etag,created_at,updated_at,name,parent_type,field_type,displayed,deleted,required,"
    "display_order,permission_level,picklist_options{id,option,deleted_at}"
)

MATTER_CONTACT = (
    "id,etag,name,first_name,middle_name,last_name,type,is_client,relationship_name,description,"
    "primary_email_address,primary_phone_number,matter_id,created_at,updated_at"
)

RELATIONSHIP = "id,etag,description,created_at,updated_at,matter{id},contact{id,name,type}"

CONTACT = ",".join([
    "id,etag,name,first_name,middle_name,last_name,date_of_birth,type,created_at,updated_at,prefix,"
    "title,initials,primary_email_address,secondary_email_address,primary_phone_number,"
    "secondary_phone_number,is_client,is_co_counsel,is_bill_recipient",
    "company{id,name}",
    "addresses{id,name,street,city,province,postal_code,country,primary}",
    "email_addresses{id,name,address,primary}",
    "phone_numbers{id,name,number,primary}",
    "web_sites{id,name,address,default_web_site}",
    CUSTOM_FIELD_VALUES,
])

NOTE = (
    "id,etag,type,subject,detail,detail_text_type,date,created_at,updated_at,time_entries_count,"
    f"matter{{id}},contact{{id,name}},author{REF}"
)

COMMUNICATION = (
    "id,etag,subject,body,type,date,time_entries_count,created_at,updated_at,received_at,"
    f"user{REF},matter{{id}},senders{PARTICIPANT},receivers{PARTICIPANT},documents{{id,name}}"
)

TASK = (
    "id,etag,name,status,description,description_text_type,priority,due_at,permission,completed_at,"
    "notify_completion,statute_of_limitations,time_estimated,created_at,updated_at,"
    f"task_type{REF},assigner{REF},matter{{id}},assignee{PARTICIPANT},assignees{PARTICIPANT}"
)

CALENDAR_ENTRY = (
    "id,etag,summary,description,location,start_at,start_date,start_time,end_at,end_date,end_time,"
    "all_day,recurrence_rule,parent_calendar_entry_id,court_rule,created_at,updated_at,permission,"
    "calendar_owner_id,start_at_time_zone,"
    f"matter{{id}},calendar_owner{REF},calendar_entry_event_type{REF},"
    "attendees{id,name,type,email}"
)

ACTIVITY = (
    "id,etag,type,date,quantity_in_hours,quantity,price,note,flat_rate,billed,on_bill,total,"
    "created_at,updated_at,reference,non_billable,non_billable_total,no_charge,"
    f"activity_description{REF},expense_category{REF},matter{{id}},user{REF},vendor{{id,name,type}},"
    "document_version{id,document_id,filename}"
)

DOCUMENT = (
    "id,etag,created_at,updated_at,deleted_at,type,locked,name,received_at,filename,size,content_type,"
    "parent{id,name,type,root},matter{id},contact{id,name},document_category{id,name},"
    "latest_document_version{id,uuid,filename,size,content_type,version_number,created_at,fully_uploaded}"
)

FOLDER = "id,etag,created_at,updated_at,deleted_at,type,locked,name,root,parent{id,name},matter{id}"

USER = (
    "id,etag,name,first_name,last_name,initials,email,enabled,roles,subscription_type,"
    "account_owner,time_zone,created_at,updated_at"
)
