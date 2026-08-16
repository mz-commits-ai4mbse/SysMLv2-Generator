# Remote Microscope Collaboration — User Workflow Notes

## Document status

Legacy workflow description captured from an earlier product discussion. It is not
an approved requirement specification.

## Normal collaboration flow

A microscope operator starts a collaboration session from the microscope workstation.

A remote expert receives access to the session and joins through the remote client.
After joining, the expert can view the current live microscope image.

If the expert wants to interact with the microscope, the expert sends a control
request. During normal operation, the microscope operator decides whether to grant
or reject that request.

When the operator grants the request, control is transferred to the remote expert.
The expert can then adjust the microscope view using the remote client.

The user interface should make the current controller obvious to both participants.

The operator can take back control when necessary. The workflow note does not define
whether this requires a request from the remote expert.

## Connection-loss behavior

If the remote expert loses the connection while holding control, remote control
authority must not remain active. The microscope should return to a locally safe
control state without waiting for the disconnected expert.

This automatic return is an exceptional recovery path. It is not described as a
normal user-initiated transfer.

## Open workflow questions

- Should the operator be able to revoke remote control immediately?
- What feedback is shown to the expert after a rejected request?
- What happens if the remote client reconnects after a control-loss event?
