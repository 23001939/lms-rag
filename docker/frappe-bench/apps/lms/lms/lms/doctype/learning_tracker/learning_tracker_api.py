import frappe
import json

@frappe.whitelist()
def get_user_learning_data():
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Please login to access learning tracker")

    tracker_name = frappe.db.get_value("Learning Tracker", {"user": user}, "name")
    if not tracker_name:
        tracker = frappe.get_doc({
            "doctype": "Learning Tracker",
            "user": user,
            "target_hours": 100,
            "year": 2024
        })
        tracker.insert(ignore_permissions=True)
        tracker_name = tracker.name

    tracker_doc = frappe.get_doc("Learning Tracker", tracker_name)

    completed_lms_courses = []
    try:
        # Check completion purely based on progress >= 100
        enrollments = frappe.get_all(
            "LMS Enrollment",
            filters={"member": user},
            fields=["course", "modified", "name", "progress"]
        )
        completed_enrollments = [e for e in enrollments if (e.get("progress") or 0) >= 100]

        for en in completed_enrollments:
            course_id = en.get("course")
            if course_id and frappe.db.exists("LMS Course", course_id):
                course_doc = frappe.get_doc("LMS Course", course_id)
                completed_lms_courses.append({
                    "course_name": course_doc.title or course_id,
                    "hours": course_doc.course_hours or 0,
                    "completion_date": str(en.get("modified")).split(" ")[0] if en.get("modified") else "",
                    "type": "LMS"
                })
    except Exception as e:
        frappe.log_error(str(e), "Learning Tracker LMS Courses Error")

    return {
        "tracker": tracker_doc,
        "completed_lms_courses": completed_lms_courses
    }

@frappe.whitelist()
def save_learning_tracker():
    doc_data = frappe.form_dict.get("doc")
    if isinstance(doc_data, str):
        doc_data = json.loads(doc_data)
    
    if not doc_data:
        frappe.throw("No data provided")

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Unauthorized")

    tracker_name = frappe.db.get_value("Learning Tracker", {"user": user}, "name")
    if tracker_name:
        tracker = frappe.get_doc("Learning Tracker", tracker_name)
        tracker.target_hours = float(doc_data.get("target_hours", tracker.target_hours))
        tracker.year = int(doc_data.get("year", tracker.year))
        
        tracker.set("external_courses", [])
        for row in doc_data.get("external_courses", []):
            if row.get("course_name"):
                tracker.append("external_courses", {
                    "doctype": "External Learning Record",
                    "course_name": row.get("course_name"),
                    "hours": float(row.get("hours") or 0),
                    "completion_date": row.get("completion_date") or None,
                    "proof_file": row.get("proof_file") or None
                })
        tracker.save(ignore_permissions=True)
    return tracker