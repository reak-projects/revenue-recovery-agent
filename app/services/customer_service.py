from uuid import uuid4

from app.database.actions import save_agent_action
from app.database.audit import save_audit_event


SUPPORTED_ACTIONS = {
	"SEND_REMINDER",
	"SEND_PAYMENT_LINK",
	"TRACK_PROMISE",
	"ESCALATE",
	"RECOVERED",
}


def execute_customer_action(
	action: str,
	case_id: str,
	customer_id: str,
	reason: str | None = None,
) -> dict:
	if action not in SUPPORTED_ACTIONS:
		raise ValueError(f"Unsupported customer action: {action}")

	action_id = str(uuid4())
	event_id = str(uuid4())
	message = f"Simulated customer action: {action}"

	save_agent_action(
		action_id=action_id,
		case_id=case_id,
		action=action,
		reason=reason,
	)

	save_audit_event(
		event_id=event_id,
		case_id=case_id,
		event_type="CUSTOMER_ACTION_EXECUTED",
		description=message,
		actor="AI_AGENT",
		metadata={
			"action": action,
			"customer_id": customer_id,
			"action_id": action_id,
			"reason": reason,
		},
	)

	return {
		"status": "EXECUTED",
		"action": action,
		"action_id": action_id,
		"message": message,
	}
