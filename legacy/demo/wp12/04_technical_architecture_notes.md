# Remote Microscope Collaboration — Technical Architecture Notes

## Document status

Informal legacy architecture notes. Component names are descriptive working names,
not approved logical architecture elements.

## Working technical concept

The microscope workstation is the local system endpoint connected to the microscope.
It is expected to initiate the collaboration session and provide the microscope image
to the collaboration software.

A remote client is used by the remote expert to receive the live image and to submit
control-related user actions.

A streaming responsibility handles distribution of the live microscope image from
the workstation side to the remote client.

A control responsibility coordinates control requests and microscope-control
authority. Remote control commands are only forwarded while the remote expert owns
control authority.

A session/audit responsibility records session lifecycle information and control
authority changes for later traceability.

The exact deployment of these responsibilities is undecided. They may be separate
services or may be combined in one or more applications. No protocol, port, cloud
provider, persistence technology, or database product is specified.

## Conceptual interactions

- workstation side provides image data to the streaming responsibility
- remote client consumes the live image stream
- remote client submits a control request to the control responsibility
- control responsibility applies the current control-authority state
- permitted remote microscope commands are routed toward the workstation
- session/audit responsibility receives session and control-authority events

## Architecture uncertainty

The notes intentionally do not decide whether the control responsibility belongs to
the workstation application, a separate backend service, or another deployment unit.
