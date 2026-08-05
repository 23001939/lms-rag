# Copyright (c) 2026, manhtv and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LMSChatHistory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		message: DF.Text | None
		name: DF.Int | None
		role: DF.Literal["user", "assistant"]
		user: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "LMS Chat History"
