# Remote Microscope Collaboration — Product Overview

## Document status

Legacy product note. The statements below are intentionally informal and incomplete.
They describe product intent, not an approved SysML model.

## Product context

The Remote Microscope Collaboration capability allows a microscope operator to share
a live microscope view with a remote expert during a session.

The microscope operator works at the microscope workstation. The remote expert joins
from a separate client application. The purpose is to support remote consultation
without requiring the expert to be physically present at the microscope.

The remote expert shall be able to observe the live microscope image. During the
session, the expert may also take temporary control of the microscope when the
operator permits it. The operator remains responsible for the local session and must
be able to understand who currently controls the microscope.

The collaboration session should retain enough session information to make later
review possible. The exact information to retain and the retention period have not
yet been agreed.

The product note does not define a network protocol, deployment architecture,
performance target, image latency target, or regulatory classification.

## Open product questions

- How long should session information be retained?
- Which connection-quality limits are acceptable?
- Which microscope functions may be controlled remotely?
