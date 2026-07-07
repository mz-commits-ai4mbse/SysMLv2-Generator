# Example Legacy Model Description

## Source Context

This file is a simple raw legacy engineering description used for the first Turing Generator MVP ingestion task.

It represents an informal engineering description of a small system.

The file is intentionally incomplete, but missing information is not explicitly listed in this input.

The goal is not to generate a complete SysML v2 model.

The goal is to test whether the Turing Generator can identify which model-relevant information is present and which downstream model artifacts may or may not be justified based on available evidence.

---

## System Name

Remote Microscope Streaming System

---

## Informal System Description

The system allows a remote user to view a live microscope image stream through a software application.

A microscope operator starts a streaming session from the microscope workstation.

A remote expert can join the session through a client application.

The remote expert can view the live image stream and may request control of the microscope.

The microscope operator can accept or reject the control request.

If control is granted, the remote expert can adjust the microscope view remotely.

The system shall prevent two users from controlling the microscope at the same time.

The system shall show who currently has control.

The system shall record basic session information for later traceability.

---

## Mentioned Users

The description mentions the following user roles:

- microscope operator
- remote expert

---

## Mentioned System Capabilities

The description mentions the following capabilities:

- start streaming session
- join streaming session
- view live microscope image
- request remote control
- accept or reject remote control request
- adjust microscope view remotely
- prevent simultaneous control
- show current control owner
- record basic session information

---

## Mentioned System Elements

The description mentions the following system elements:

- microscope workstation
- software application
- client application
- live image stream
- control request
- session information

---

## Mentioned Constraints

The description mentions the following constraints:

- only one user may control the microscope at a time
- control transfer requires acceptance by the microscope operator
- the current control owner must be visible

---

## Informal Notes

The description focuses on user interaction, remote viewing and control transfer.

The description mentions some software and workstation elements, but does not describe deployment, interfaces, performance, validation or regulatory context in detail.