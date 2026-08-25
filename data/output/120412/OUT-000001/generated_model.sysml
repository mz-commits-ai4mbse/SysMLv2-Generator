package GeneratedModel {
    package StakeholderLevel {
        package Stakeholders {
            part def IME_000001 {
                doc /* Engineering name: Microscope Operator
            Description:
            Local person working at the microscope workstation and responsible for the local session. */
            }
            part def IME_000003 {
                doc /* Engineering name: Remote Expert
            Description:
            Person who joins from a separate client application and participates remotely in the session. */
            }
        }
        package UserNeeds {
        }
        package StakeholderRequirements {
            requirement IME_000007 {
                doc /* Engineering name: Remote Expert Physical Presence Not Required
            Description:
            Remote consultation shall not require the remote expert to be physically present at the microscope. */
            }
            requirement IME_000010 {
                doc /* Engineering name: Operator Permission for Temporary Control
            Description:
            Temporary microscope control by the remote expert shall require operator permission. */
            }
            requirement IME_000011 {
                doc /* Engineering name: Operator Responsibility for Local Session
            Description:
            The microscope operator shall remain responsible for the local session. */
            }
            requirement IME_000012 {
                doc /* Engineering name: Current Microscope Controller Identification
            Description:
            Users shall be able to identify who currently controls the microscope. */
            }
            requirement IME_000013 {
                doc /* Engineering name: Later Review Availability
            Description:
            Later review shall be possible. */
            }
        }
        package UseCases {
            use case def IME_000006 {
                doc /* Engineering name: Remote Consultation
            Description:
            Support consultation with a remote participant. */
            }
        }
    }
    package SystemLevel {
        package Requirements {
        }
        package Functional {
            action IME_000002 {
                doc /* Engineering name: Share Live Microscope View
            Description:
            Share a live microscope view with a remote expert during a session. */
            }
            action IME_000008 {
                doc /* Engineering name: Observe Live Microscope Image
            Description:
            The remote expert is able to observe the live microscope image. */
            }
            action IME_000009 {
                doc /* Engineering name: Take Temporary Microscope Control
            Description:
            The remote expert may take temporary control of the microscope when permitted by the operator. */
            }
        }
        package Logical {
        }
        package Physical {
        }
    }
    package SubsystemLevel {
        package Requirements {
        }
        package Functional {
        }
        package Logical {
            part IME_000005 {
                doc /* Engineering name: Separate Client Application
            Description:
            Client application used by the remote expert to join the session. */
            }
        }
        package Physical {
            part IME_000004 {
                doc /* Engineering name: Microscope Workstation
            Description:
            Local workstation where the microscope operator works. */
            }
        }
    }

    dependency from SubsystemLevel::Physical::IME_000004 to SubsystemLevel::Logical::IME_000005;
}
